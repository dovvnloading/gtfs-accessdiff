# Security policy

The current code is a prototype. Only analyze GTFS files you trust or are
allowed to inspect. ZIPs are processed locally; the program does not execute
code from them and reads only a root-level `stops.txt` with an upper size bound.

Do not attach secrets, private feeds, or unpublished infrastructure details to
public issues. For a security issue, contact the repository maintainer privately
once this project has a published GitHub repository and a security contact.

Before production deployment, add fuzzing, malformed archive tests, dependency
pinning in example CI workflows, and a documented threat model.
