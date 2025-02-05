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

  function sendResponse(output) {
    console.log(output);
    document.getElementById("answer").innerHTML = output;
  }

  const responses = {
    age: "You need to be at least 17 years old to join the Army. If you are older than 35 years old, certain jobs may apply to you. <a href='https://www.goarmy.com/how-to-join/steps' target='_blank'>See all the steps to join</a>",
    basic_general:
      "Weeks 1 – 2 In this first phase, you’ll start to adapt to Army life and learn about discipline, teamwork, Army programs, traditions, and more.",
    basic_toughness:
      "Basic Training is challenging and meant to push you to become the best version of yourself. It will help you develop mentally and physically to overcome things you didn’t think possible. You’ll also realize that the military and Drill Sergeants are not here to break you. Their goal is to build you up, help you find your inner strength, and teach you to succeed in both the Army and everyday life.",
    basic_length:
      "Basic Training lasts approximately 10 weeks and varies slightly based on your Military Occupational Specialty (MOS).",
    recruiter: "Let's talk with a recruiter - Open Live Chat",
    basic_eating:
      "Typically, you’ll eat in the dining facility (DFAC), which is the Army’s version of a chow hall or cafeteria. There may be instances when you’ll eat out in the field, in which case meals are brought along. Other times, you might eat pre-packaged Meals, Ready-to-Eat (MREs).",
  };

  const commands = [
    {
      keyword: "how old",
      text: responses.age,
      specificity: 2,
    },
    {
      keyword: "basic training",
      text: responses.basic_general,
      specificity: 1,
    },
    {
      keyword: "basic training hard",
      text: responses.basic_toughness,
      specificity: 2,
    },
    {
      keyword: "hard is basic training",
      text: responses.basic_toughness,
      specificity: 2,
    },
    {
      keyword: "how long basic training",
      text: responses.basic_length,
      specificity: 2,
    },
    {
      keyword: "talk with",
      text: responses.recruiter,
      specificity: 2,
    },
    {
      keyword: "Where do you eat while in Basic Training",
      text: responses.basic_eating,
      specificity: 1,
    },
  ];

  const SIMILARITY_THRESHOLD = 0.4;

  // Remove common stop words for better matching
  function preprocess(text) {
    const stopWords = ["do", "i", "to", "the", "a", "is", "and", "you", "be"];
    return text
      .toLowerCase()
      .split(" ")
      .filter((word) => !stopWords.includes(word))
      .join(" ");
  }

  // Calculate string similarity using Dice Coefficient
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

    // Find best match
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
        (a, b) =>
          b.exactMatch - a.exactMatch ||
          b.similarity - a.similarity ||
          b.specificity - a.specificity
      )[0];

    if (bestMatch) {
      console.log(
        `Executing: ${
          bestMatch.keyword
        } (Similarity: ${bestMatch.similarity.toFixed(2)})`
      );
      sendResponse(bestMatch.text);
    } else {
      console.log("No matching command found.");
      sendResponse("No matching command found. Sending text to Search");
      window.open("https://www.goarmy.com/search?fulltext=" + transcript);
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
  };
} else {
  console.error("Speech recognition not supported in this browser.");
}
