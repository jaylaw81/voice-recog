// Add these constants at the top of your code
const CACHE_TTL = 3600000; // 1 hour cache duration
const CACHE_KEY = "faqCache";

if (navigator.mediaDevices.getUserMedia) {
  const startButton = document.getElementById("startButton");
  const canvas = document.getElementById("visualizer");
  const canvasCtx = canvas.getContext("2d");

  let audioContext, analyser, microphone, dataArray, animationFrameId, stream;

  startButton.addEventListener("click", async () => {
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 1024; // Higher resolution for smooth waveforms

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      microphone = audioContext.createMediaStreamSource(stream);
      microphone.connect(analyser);

      dataArray = new Uint8Array(analyser.fftSize);

      visualize();
    }
  });

  function visualize() {
    requestAnimationFrame(visualize);
    analyser.getByteTimeDomainData(dataArray);

    canvasCtx.clearRect(0, 0, canvas.width, canvas.height); // Transparent background

    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = "rgba(0, 200, 255, 0.8)"; // Light blue waveform
    canvasCtx.beginPath();

    let sliceWidth = canvas.width / dataArray.length;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
      let v = dataArray[i] / 128.0;
      let y = (v * canvas.height) / 2;

      if (i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    canvasCtx.stroke();
  }
} else {
  console.error("getUserMedia not supported in this browser.");
}

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
    document.querySelector("#startButton").classList.add("bg-red-500");
    document.querySelector("#visualizer").style.display = "block";
  });

  function sendResponse(output, sourceUrl, image) {
    console.log(output);
    document.getElementById(
      "answer"
    ).innerHTML = `${output} <br><a class='mt-8 inline-block bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full' href='${sourceUrl}#:~:text=${output}' target='_blank'>See the full answer</a>`;

    document.getElementById(
      "image"
    ).innerHTML = `<img src="https://www.goarmy.com${image}" />`;

    document.querySelector("#startButton").classList.remove("bg-red-500");
    document.querySelector("#visualizer").style.display = "none";

    let stream;

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then(function (mediaStream) {
        stream = mediaStream;
      })
      .catch(function (error) {
        console.error("Error accessing microphone:", error);
      });

    if (stream) {
      stream.getAudioTracks().forEach((track) => track.stop());
      stream = null; // Optionally release the stream reference
    }
  }

  let commands = [];
  const SIMILARITY_THRESHOLD = 0.4;

  async function loadCommands() {
    try {
      // Try to get cached data
      const cachedData = localStorage.getItem(CACHE_KEY);
      const now = Date.now();

      startButton.disabled = true;
      startButton.textContent = "Loading Data...Please wait";
      startButton.classList.add("bg-gray-400");

      if (cachedData) {
        const { timestamp, data } = JSON.parse(cachedData);

        // Use cache if it's still valid
        if (now - timestamp < CACHE_TTL) {
          commands = processData(data);
          console.log("Using cached commands");
          startButton.disabled = false;
          startButton.textContent = "Ask a Question";
          startButton.classList.add("bg-blue-500");
          startButton.classList.remove("bg-gray-400");
          return;
        }
      }

      // Fetch fresh data if cache is expired or missing
      const response = await fetch("http://127.0.0.1:5000/api/faqs");
      const data = await response.json();

      // Update cache
      localStorage.setItem(
        CACHE_KEY,
        JSON.stringify({
          timestamp: now,
          data: data,
        })
      );

      commands = processData(data);
      console.log("Commands loaded and cached");
      startButton.disabled = false;
      startButton.textContent = "Ask a Question";
      startButton.classList.add("bg-blue-500");
      startButton.classList.remove("bg-gray-400");
    } catch (error) {
      console.error("Error fetching FAQ data:", error);

      // Fall back to cache if available
      const cachedData = localStorage.getItem(CACHE_KEY);
      if (cachedData) {
        console.log("Using stale cache due to API error");
        commands = processData(JSON.parse(cachedData).data);
        startButton.disabled = false;
        startButton.textContent = "Ask a Question";
        startButton.classList.add("bg-blue-500");
      }
    }
  }

  // Add this helper function
  function processData(data) {
    return data.map((item) => ({
      keyword: item.question.toLowerCase(),
      text: item.answer,
      sourceUrl: item.source_url,
      image: item.image,
    }));
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

    const matches = commands.map((command) => ({
      ...command,
      similarity: getSimilarity(
        processedTranscript,
        preprocess(command.keyword)
      ),
      keywordMatch: preprocess(command.keyword)
        .split(" ")
        .some((word) => processedTranscript.includes(word)), // Check if any keyword matches
    }));

    // Find the best match based on exact match, similarity, or loose keyword matching
    const bestMatch = matches
      .filter(
        (command) =>
          command.exactMatch ||
          command.similarity >= SIMILARITY_THRESHOLD ||
          command.keywordMatch
      )
      .sort((a, b) => {
        // Prioritize exact matches, then similarity, then keyword matches
        if (b.exactMatch !== a.exactMatch) return b.exactMatch - a.exactMatch;
        if (b.similarity !== a.similarity) return b.similarity - a.similarity;
        return b.keywordMatch - a.keywordMatch;
      })[0];

    if (bestMatch) {
      console.log(
        `Executing: ${
          bestMatch.keyword
        } (Similarity: ${bestMatch.similarity.toFixed(2)})`
      );
      sendResponse(bestMatch.text, bestMatch.sourceUrl, bestMatch.image);
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

  recognition.onspeechend = () => {
    recognition.stop();
    console.log("Speech recognition has stopped.");
  };

  loadCommands();
} else {
  console.error("Speech recognition not supported in this browser.");
}
