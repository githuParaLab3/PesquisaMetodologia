# Java 21 LTS — G1GC (padrão JDK 21, conforme pré-projeto)
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -q
COPY src ./src
RUN mvn package -DskipTests -q

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
# G1GC é o padrão do JDK 21 — explicitado conforme metodologia
ENV JAVA_OPTS="-XX:+UseG1GC -Xms128m -Xmx384m -Djava.security.egd=file:/dev/./urandom"
COPY --from=builder /app/target/error-perf-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["sh","-c","java $JAVA_OPTS -jar app.jar"]
