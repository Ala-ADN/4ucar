"""External system adapters (Scopus, Google Scholar, MESRS, Twilio, …).

Each integration is one module that maps an external API into our internal
typed inputs (e.g. `FacultyMember`, `Publication`). Calculators stay
ignorant of where the data came from.
"""
