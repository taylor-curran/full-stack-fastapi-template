# Karate API tests

Black-box BDD-style API tests for the FastAPI backend, written with
[Karate](https://github.com/karatelabs/karate). The tests live alongside the
backend so they ship with the repo, but they run against the backend over HTTP
the same way an external client would — there is no in-process coupling.

## Layout

```
backend/karate/
├── pom.xml
└── src/test/
    ├── java/karate/KarateRunner.java        # JUnit 5 entry point
    └── resources/
        ├── karate-config.js                 # env + credential resolution
        ├── helpers/                         # callonce-able feature helpers
        │   ├── login.feature
        │   └── signup-user.feature
        └── features/                        # actual scenarios
            ├── auth.feature
            ├── items.feature
            └── users.feature
```

`KarateRunner` exposes two entry points:

- `runAll()` — `@Karate.Test`, used from IDEs (sequential, easy to read logs).
- `runParallel()` — `@Test`, used by Surefire / CI. Runs every feature with
  4-way parallelism and emits a Cucumber-JSON report under
  `target/karate-reports/`.

## Prerequisites

- JDK 17+ (CI uses 17; 21 also works locally).
- Maven 3.9+.
- A running backend on `http://localhost:8000` (any URL works, see below).

## Starting the backend

The tests do not bring the backend up themselves — start it however you
normally would. The simplest path mirrors what the rest of the repo uses:

```bash
# from the repo root, bring up just the API + its dependencies
docker compose up -d db mailcatcher backend
```

Confirm it's reachable before running the suite:

```bash
curl -sf http://localhost:8000/api/v1/utils/health-check/ && echo OK
```

## Running the suite

From `backend/karate/`:

```bash
mvn -B test
```

That defaults to `http://localhost:8000` + `/api/v1` and the local-dev admin
credentials. To point it elsewhere, override any of these `-D` properties:

| Property        | Default                    | Notes                                    |
| --------------- | -------------------------- | ---------------------------------------- |
| `backendUrl`    | `http://localhost:8000`    | Scheme + host + port, no trailing slash. |
| `apiPath`       | `/api/v1`                  | Mounted under `backendUrl`.              |
| `adminEmail`    | `admin@example.com`        | Required when `karate.env != local`.     |
| `adminPassword` | `changethis`               | Required when `karate.env != local`.     |
| `karate.env`    | `local`                    | See "Environments" below.                |

Example, against a deployed staging backend:

```bash
mvn -B test \
  -Dkarate.env=staging \
  -DbackendUrl=https://staging.example.com \
  -DadminEmail=admin@example.com \
  -DadminPassword="$STAGING_ADMIN_PASSWORD"
```

### Environments

`karate-config.js` only auto-fills `adminEmail` / `adminPassword` when
`karate.env=local`. For any other env, both must be supplied explicitly via
`-D` properties — otherwise the suite fails fast at config time. This is
deliberate: it stops a stray `mvn test` from authenticating against a
non-local backend with the well-known dev password `changethis`.

## Running a single feature or scenario

```bash
# Just the items feature
mvn -B test -Dkarate.options="classpath:features/items.feature"

# A single scenario by line number
mvn -B test -Dkarate.options="classpath:features/items.feature:6"

# Tag-based filtering (e.g. only @smoke)
mvn -B test -Dkarate.options="--tags @smoke classpath:features"
```

## Reports

After a run, open:

```
backend/karate/target/karate-reports/karate-summary.html
```

`runParallel()` also produces Cucumber-JSON output in the same directory,
which can be fed into a downstream reporter (Cluecumber, ReportPortal, etc.).

## Notes / gotchas

- Karate is pinned to **1.4.1**. See the inline comment in `pom.xml` before
  bumping it.
- `slf4j-simple` is included as a test-scope dependency so Karate's
  per-request HTTP logs surface during runs. Without an SLF4J binding those
  logs are silently dropped.
- Helpers under `helpers/` are tagged `@ignore` so the runner doesn't pick
  them up as standalone scenarios; they're meant to be invoked via
  `call` / `callonce`.
