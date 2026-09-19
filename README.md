# Fieldnote

An original mobile interaction prototype by Pururin, built with AI-assisted design and coding. This is a self-initiated portfolio concept, not client work or a live AI product.

Flow: sample or original note → scripted clarification → editable structured review → local save → Markdown export. The sample is synthetic. Custom observations are kept verbatim; the demo does not pretend to extract arbitrary data automatically. No account, dependencies, external fonts, analytics, network API or paid service.

Run with `python -m http.server 8768 --bind 127.0.0.1` in this directory, then open `http://127.0.0.1:8768/`. The three app files can be hosted by any static host. Save record writes the latest record to this browser's local storage; Download Markdown exports it. Clearing site data removes the local copy.

Temperature change is end minus start, rounded to six decimal places to avoid binary floating-point display noise. Missing values remain Not recorded. No scientific uncertainty or validation is inferred.

Scope: interaction and responsive front-end demonstration. Production integration, actual AI extraction, authentication, cloud persistence and a Figma source file are not included.
