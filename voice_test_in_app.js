// Simple test to verify voice functionality in the actual application context
console.log('Voice Test in App Context');

// Check if speech synthesis is supported
if ('speechSynthesis' in window) {
  console.log('✅ Speech synthesis is supported');
  
  // Try to get voices
  const voices = speechSynthesis.getVoices();
  console.log('Available voices:', voices.length);
  
  if (voices.length > 0) {
    console.log('Voice details:');
    voices.forEach((voice, index) => {
      console.log(`${index + 1}. ${voice.name} (${voice.lang}) ${voice.default ? '[DEFAULT]' : ''}`);
    });
    
    // Test speaking
    console.log('Testing speech...');
    const speech = new SpeechSynthesisUtterance('Hello, this is a test of the text-to-speech functionality.');
    speech.lang = 'en-US';
    speech.volume = 1;
    speech.rate = 1;
    speech.pitch = 1;
    
    speech.onstart = function(event) {
      console.log('✅ Speech started');
    };
    
    speech.onend = function(event) {
      console.log('✅ Speech ended successfully');
    };
    
    speech.onerror = function(event) {
      console.error('❌ Speech error:', event.error);
    };
    
    speechSynthesis.speak(speech);
    console.log('Speech command sent');
  } else {
    console.log('⚠️ No voices available yet. This is common on first load.');
    console.log('Trying again in 2 seconds...');
    
    setTimeout(() => {
      const voices = speechSynthesis.getVoices();
      console.log('Voices after delay:', voices.length);
      if (voices.length > 0) {
        console.log('Testing speech after delay...');
        const speech = new SpeechSynthesisUtterance('Hello, this is a delayed test.');
        speech.lang = 'en-US';
        speechSynthesis.speak(speech);
      }
    }, 2000);
  }
} else {
  console.log('❌ Speech synthesis is NOT supported in this browser');
}

// Test localStorage voice retrieval
const savedVoice = localStorage.getItem('selectedVoice');
console.log('Saved voice in localStorage:', savedVoice);

// Test voice selection if saved
if (savedVoice) {
  console.log('Testing with saved voice...');
  const speech = new SpeechSynthesisUtterance('Testing with your saved voice preference.');
  speech.lang = 'en-US';
  
  const voices = speechSynthesis.getVoices();
  const selectedVoice = voices.find(voice => voice.name === savedVoice);
  if (selectedVoice) {
    speech.voice = selectedVoice;
    console.log('Using saved voice:', selectedVoice.name);
    speechSynthesis.speak(speech);
  } else {
    console.log('Saved voice not found in available voices');
  }
}