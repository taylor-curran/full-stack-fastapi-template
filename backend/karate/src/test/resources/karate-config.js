function fn() {
  const env = karate.env || "local";
  const backendUrl = karate.properties["backendUrl"] || "http://localhost:8000";
  const apiPath = karate.properties["apiPath"] || "/api/v1";

  const config = {
    env: env,
    baseUrl: backendUrl + apiPath,
    adminEmail: karate.properties["adminEmail"] || "admin@example.com",
    adminPassword: karate.properties["adminPassword"] || "changethis",
  };

  return config;
}
