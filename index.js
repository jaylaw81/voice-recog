// Check for browser compatibility
if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
  const recognition = new (window.SpeechRecognition ||
    window.webkitSpeechRecognition)();

  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 3;

  const startButton = document.getElementById("startButton");
  startButton.addEventListener("click", () => {
    recognition.start();
  });

  function sendResponse(output, sourceUrl) {
    console.log(output);
    document.getElementById(
      "answer"
    ).innerHTML = `${output} <br><a href='${sourceUrl}' target='_blank'>Source</a>`;
  }

  let commands = [];
  const SIMILARITY_THRESHOLD = 0.4;

  async function loadCommands() {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/faqs");
      const data = await response.json();
      commands = data.map((item) => ({
        keyword: item.question.toLowerCase(),
        text: item.answer,
        sourceUrl: item.source_url,
      }));
      console.log("Commands loaded:", commands);
    } catch (error) {
      console.error("Error fetching FAQ data:", error);
    }
  }

  function preprocess(text) {
    const stopWords = ["do", "i", "to", "the", "a", "is", "and", "you", "be"];
    return text
      .toLowerCase()
      .split(" ")
      .filter((word) => !stopWords.includes(word))
      .join(" ");
  }

  function getSimilarity(str1, str2) {
    const bigrams = (s) => {
      const result = [];
      for (let i = 0; i < s.length - 1; i++) {
        result.push(s[i] + s[i + 1]);
      }
      return result;
    };

    const bigrams1 = bigrams(str1.toLowerCase());
    const bigrams2 = bigrams(str2.toLowerCase());
    const matches = bigrams1.filter((bigram) =>
      bigrams2.includes(bigram)
    ).length;

    return (2 * matches) / (bigrams1.length + bigrams2.length);
  }

  recognition.onresult = (event) => {
    let transcript = event.results[0][0].transcript.toLowerCase();
    const confidence = (event.results[0][0].confidence * 100).toFixed(2);

    const processedTranscript = preprocess(transcript);

    document.getElementById("result").textContent = transcript;
    document.getElementById("confidence").textContent = confidence;

    const matches = commands.map((command) => ({
      ...command,
      similarity: getSimilarity(
        processedTranscript,
        preprocess(command.keyword)
      ),
      exactMatch: processedTranscript === preprocess(command.keyword),
    }));

    const bestMatch = matches
      .filter(
        (command) =>
          command.exactMatch || command.similarity >= SIMILARITY_THRESHOLD
      )
      .sort(
        (a, b) => b.exactMatch - a.exactMatch || b.similarity - a.similarity
      )[0];

    if (bestMatch) {
      console.log(
        `Executing: ${
          bestMatch.keyword
        } (Similarity: ${bestMatch.similarity.toFixed(2)})`
      );
      sendResponse(bestMatch.text, bestMatch.sourceUrl);
    } else {
      console.log("No matching command found.");
      sendResponse(
        "No matching command found. Sending text to Search",
        "https://www.goarmy.com/search?fulltext=" + transcript
      );
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
  };

  loadCommands();
} else {
  console.error("Speech recognition not supported in this browser.");
}
