"""Off-fleet experiment code.

Nothing here is imported by ``glee_agent``, ``sim``, ``scripts`` or ``tests``
unless the fleet owner explicitly wires it in (see ``assign.SPEC`` for the
two-call integration). The package is stdlib-only and every public entry point
is total: it returns a falsy "not handled" rather than raising, so a bug in the
experiment can never cost a live turn.
"""
