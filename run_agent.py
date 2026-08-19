#!/usr/bin/env python
"""Entry point: play GLEE Competition games until stopped.

    export GLEE_API_KEY=glee_...
    python run_agent.py                     # play all three families, forever
    python run_agent.py --max-games 20      # a bounded session
    python run_agent.py --families bargaining --llm-mode off

Every knob is also an environment variable — see glee_agent/config.py.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from glee_sdk import (
    CompetitionClosedError,
    CompetitionNotOpenError,
    GleeAPIError,
    GleeClient,
)

from glee_agent import llm
from glee_agent.config import Config
from glee_agent.gamelog import GameLog
from glee_agent.probes import PROBES, make_probe

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)-7s %(name)s %(message)s")
logger = logging.getLogger("glee.run")


def parse_args(cfg: Config) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--families", default=",".join(cfg.families),
                        help="comma-separated: bargaining,negotiation,persuasion")
    parser.add_argument("--concurrency", type=int, default=cfg.concurrency,
                        help="games in flight at once (4-10; 60 req/min is the cap)")
    parser.add_argument("--poll-interval", type=float, default=cfg.poll_interval)
    parser.add_argument("--max-games", type=int, default=cfg.max_games)
    parser.add_argument("--max-time", type=float, default=cfg.max_time,
                        help="seconds; in-flight games always finish first")
    parser.add_argument("--llm-mode", choices=("off", "messages", "full"),
                        default=cfg.llm_mode)
    parser.add_argument("--llm-model", default=cfg.llm_model)
    parser.add_argument("--llm-max-calls", type=int, default=cfg.llm_max_calls,
                        help="hard spend cap; 0 means unlimited")
    parser.add_argument("--log-dir", default=cfg.log_dir)
    parser.add_argument("--probe", default="champion", choices=sorted(PROBES),
                        help="which policy to play (see glee_agent/probes.py)")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed for the randomized probe")
    parser.add_argument("--quiet", action="store_true", help="warnings and errors only")
    return parser.parse_args()


def main() -> int:
    cfg = Config.from_env()
    args = parse_args(cfg)

    cfg.families = tuple(f.strip() for f in args.families.split(",") if f.strip())
    cfg.concurrency = args.concurrency
    cfg.poll_interval = args.poll_interval
    cfg.max_games = args.max_games
    cfg.max_time = args.max_time
    cfg.llm_mode = args.llm_mode
    cfg.llm_model = args.llm_model
    cfg.llm_max_calls = args.llm_max_calls
    cfg.log_dir = args.log_dir

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    if not cfg.api_key:
        print("Set GLEE_API_KEY (get one from https://glee-competition.com/dashboard)",
              file=sys.stderr)
        return 1

    client = (GleeClient(api_key=cfg.api_key, base_url=cfg.base_url)
              if cfg.base_url else GleeClient(api_key=cfg.api_key))

    try:
        # /stats is not competition-gated, so this proves the key works even
        # before matchmaking opens.
        logger.info("Agent stats: %s", client.stats())
    except GleeAPIError as exc:
        logger.error("Could not reach the platform: %s", exc)
        return 1

    log = GameLog(cfg.log_dir)
    strategy, probe_cfg = make_probe(args.probe, cfg, log, seed=args.seed)
    logger.info("Playing %s | probe=%s | concurrency=%d | llm=%s (%s) | logs=%s",
                ", ".join(cfg.families), args.probe, cfg.concurrency, cfg.llm_mode,
                cfg.llm_model if cfg.llm_mode != "off" else "-", cfg.log_dir)

    exit_code = 0
    try:
        client.run(strategy,
                   game_families=list(cfg.families),
                   poll_interval=cfg.poll_interval,
                   max_games=cfg.max_games,
                   max_time=cfg.max_time,
                   concurrency=cfg.concurrency)
    except CompetitionNotOpenError as exc:
        logger.warning("Setup is fine — the competition opens at %s",
                       exc.competition_open_at)
    except CompetitionClosedError as exc:
        logger.warning("The competition closed at %s", exc.competition_close_at)
    except KeyboardInterrupt:
        logger.info("Interrupted — leaving the queue so no game is matched to a "
                    "stopped agent.")
        exit_code = 130
    except GleeAPIError as exc:
        # The platform suspends queue joins for ~30 minutes when an agent's last
        # three games all timed out on its turn. Exiting turns that into a
        # crash-loop: the supervisor restarts, the API refuses again, and the
        # backoff escalates to 5 minutes, so recovery lags the ban by ages.
        # Waiting in place means the agent rejoins the moment the ban lifts.
        cooldown = exc.status_code == 403 and "timed out" in str(exc).lower()
        if cooldown:
            logger.warning("Queue joins suspended (crash-loop cooldown). Waiting "
                           "in place and retrying every 60s: %s", exc)
            while True:
                time.sleep(60)
                try:
                    client.queue(cfg.families[0])
                    client.leave_queue()
                    logger.info("Cooldown lifted; resuming play.")
                    break
                except GleeAPIError as retry_exc:
                    if not (retry_exc.status_code == 403
                            and "timed out" in str(retry_exc).lower()):
                        logger.error("API error while waiting: %s", retry_exc)
                        return 1
                except KeyboardInterrupt:
                    return 130
            return main()          # re-enter with a clean run loop
        logger.error("API error: %s", exc)
        exit_code = 1
    finally:
        # run() leaves the queue on every exit path, but a KeyboardInterrupt
        # during a poll can land outside it. Leaving twice is a harmless no-op,
        # and an agent left queued gets matched into games it then times out.
        try:
            client.leave_queue()
        except Exception:
            pass
        if cfg.llm_mode != "off":
            logger.info("LLM usage: %s", llm.stats())
        try:
            written = log.finalize(client)
            logger.info("Recorded %d game results to %s", written, log.results_path)
        except Exception:
            logger.exception("Could not record game results")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
