package karate;

import com.intuit.karate.Results;
import com.intuit.karate.Runner;
import com.intuit.karate.junit5.Karate;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class KarateRunner {

    /**
     * IDE-friendly entry point that runs every feature under the
     * `classpath:features` package sequentially. Useful while authoring
     * scenarios from the IDE, where the parallel runner below tends to
     * interleave logs in a way that makes debugging awkward.
     */
    @Karate.Test
    Karate runAll() {
        return Karate.run("classpath:features");
    }

    /**
     * CI / Maven entry point. Uses Karate's recommended parallel runner
     * pattern so the suite scales as new features are added, and emits a
     * Cucumber-JSON report under target/karate-reports/ that can later be
     * fed into a reporter.
     *
     * Surefire picks this up via the `**\/*Runner.java` include in the POM.
     */
    @Test
    void runParallel() {
        Results results = Runner.path("classpath:features")
                .outputCucumberJson(true)
                .parallel(4);
        assertEquals(0, results.getFailCount(), results.getErrorMessages());
    }
}
