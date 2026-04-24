function fn() {
  // `karate.env` selects a logical environment. Today only `local` is
  // wired through to actual baseUrl/credential defaults; other env values
  // must supply every credential explicitly via -D properties so we never
  // accidentally hit a non-local backend with the well-known dev password.
  const env = karate.env || "local";

  const backendUrl = karate.properties["backendUrl"] || "http://localhost:8000";
  const apiPath = karate.properties["apiPath"] || "/api/v1";

  const adminEmail = karate.properties["adminEmail"];
  const adminPassword = karate.properties["adminPassword"];

  if (env === "local") {
    // Local-dev defaults that match the values shipped in the repo's
    // sample .env. Safe to default because they only authenticate against
    // a developer's local backend.
    var resolvedAdminEmail = adminEmail || "admin@example.com";
    var resolvedAdminPassword = adminPassword || "changethis";
  } else {
    if (!adminEmail) {
      karate.fail(
        "adminEmail must be supplied via -DadminEmail when karate.env != 'local' (was '" +
          env +
          "')",
      );
    }
    if (!adminPassword) {
      karate.fail(
        "adminPassword must be supplied via -DadminPassword when karate.env != 'local' (was '" +
          env +
          "')",
      );
    }
    var resolvedAdminEmail = adminEmail;
    var resolvedAdminPassword = adminPassword;
  }

  return {
    env: env,
    baseUrl: backendUrl + apiPath,
    adminEmail: resolvedAdminEmail,
    adminPassword: resolvedAdminPassword,
  };
}
