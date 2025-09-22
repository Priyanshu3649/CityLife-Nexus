// Test script to verify place picker functionality
async function testPlacePicker() {
  console.log('Testing place picker functionality...');
  
  // Test autocomplete
  try {
    console.log('1. Testing autocomplete API...');
    const autocompleteResponse = await fetch('http://localhost:8000/api/v1/maps/autocomplete?query=Nar');
    console.log('Autocomplete status:', autocompleteResponse.status);
    
    if (autocompleteResponse.ok) {
      const autocompleteData = await autocompleteResponse.json();
      console.log('Autocomplete data:', JSON.stringify(autocompleteData, null, 2));
      
      if (autocompleteData.predictions && autocompleteData.predictions.length > 0) {
        const firstPrediction = autocompleteData.predictions[0];
        console.log('First prediction:', firstPrediction.description);
        
        // Test geocoding
        console.log('2. Testing geocode API...');
        const geocodeResponse = await fetch(`http://localhost:8000/api/v1/maps/geocode?address=${encodeURIComponent(firstPrediction.description)}`);
        console.log('Geocode status:', geocodeResponse.status);
        
        if (geocodeResponse.ok) {
          const geocodeData = await geocodeResponse.json();
          console.log('Geocode data:', JSON.stringify(geocodeData, null, 2));
          
          if (geocodeData.coordinates) {
            console.log('SUCCESS: Place picker is working correctly!');
            console.log('Location:', firstPrediction.description);
            console.log('Coordinates:', geocodeData.coordinates);
            return true;
          }
        } else {
          console.error('Geocode API failed with status:', geocodeResponse.status);
        }
      }
    } else {
      console.error('Autocomplete API failed with status:', autocompleteResponse.status);
    }
  } catch (error) {
    console.error('Error testing place picker:', error);
  }
  
  console.log('Place picker test completed.');
  return false;
}

// Run the test
testPlacePicker();