package karate;

import com.intuit.karate.junit5.Karate;

class KarateRunner {

    @Karate.Test
    Karate runAll() {
        return Karate.run("classpath:features");
    }
}
