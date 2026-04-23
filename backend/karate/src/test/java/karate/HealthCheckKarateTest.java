package karate;

import com.intuit.karate.junit5.Karate;

class HealthCheckKarateTest {

    @Karate.Test
    Karate testHealthCheck() {
        return Karate.run("health-check").relativeTo(getClass());
    }
}
