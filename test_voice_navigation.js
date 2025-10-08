// Simple test to verify voice navigation functionality
console.log('Testing voice navigation functionality...');

// Check if speech synthesis is supported
if ('speechSynthesis' in window) {
  console.log('✓ Speech synthesis is supported');
  
  // Try to get voices
  const voices = speechSynthesis.getVoices();
  console.log(`Found ${voices.length} voices`);
  
  if (voices.length > 0) {
    console.log('✓ Voices available');
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
      console.log('Speech started');
    };
    
    speech.onend = function(event) {
      console.log('Speech ended');
    };
    
    speech.onerror = function(event) {
      console.error('Speech error:', event);
    };
    
    speechSynthesis.speak(speech);
  } else {
    console.log('⚠️ No voices available yet. This is common on first load.');
    // Try again after a delay
    setTimeout(() => {
      const voices = speechSynthesis.getVoices();
      console.log('Voices after delay:', voices.length);
      if (voices.length > 0) {
        console.log('✓ Voices now available');
      }
    }, 1000);
  }
} else {
  console.log('✗ Speech synthesis is not supported in this browser');
}

// Test navigation instructions
const testInstructions = [
  "Take left after 300 meters",
  "Speed up to catch green light in 300 meters",
  "Slow down to avoid waiting at traffic light"
];

console.log('Testing navigation instructions...');
testInstructions.forEach((instruction, index) => {
  console.log(`${index + 1}. ${instruction}`);
});