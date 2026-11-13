FROM eclipse-temurin:21-jdk-jammy
WORKDIR /app
COPY Main.java .
RUN javac Main.java
CMD ["sh", "-c", "javac Main.java && java Main"]
