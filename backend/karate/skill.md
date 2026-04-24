# Skill: Add new Karate tests when needed

Use this guide when changing backend API behavior.

## Add a new Karate test when

- You add or change an HTTP endpoint, request schema, or response schema.
- You change auth/permission behavior (who can call what).
- You fix a bug that can be reproduced via API requests.
- You introduce a new edge case (validation, error mapping, pagination/filtering behavior).

Do **not** add a new feature file for tiny variants; prefer extending an existing scenario table unless the behavior is a new workflow.

## Where tests go

- Main scenarios: `src/test/resources/features/*.feature`
- Reusable setup flows: `src/test/resources/helpers/*.feature` (tag helpers with `@ignore`)

## Minimal authoring pattern

1. Prefer extending the nearest existing `*.feature`.
2. Keep scenario names behavior-focused (not implementation-focused).
3. Assert status code + key response fields (and error payloads for failure paths).
4. Cover at least one happy path and one meaningful failure path for new behavior.

## Run before opening PR

From `backend/karate/`:

```bash
mvn -B test
```

Optional targeted run:

```bash
mvn -B test -Dkarate.options="classpath:features/<file>.feature"
```
