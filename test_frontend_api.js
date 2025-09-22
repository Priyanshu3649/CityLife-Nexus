// Test script to verify frontend API calls
async function testApiCall() {
  try {
    console.log('Testing API call to backend...');
    const response = await fetch('http://127.0.0.1:8000/api/v1/maps/autocomplete?query=Nar');
    console.log('Response status:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('Data received:', JSON.stringify(data, null, 2));
      console.log('Number of predictions:', data.predictions?.length || 0);
      
      if (data.predictions && data.predictions.length > 0) {
        console.log('First prediction:', data.predictions[0].description);
      }
    } else {
      console.error('API call failed with status:', response.status);
    }
  } catch (error) {
    console.error('Error during API call:', error);
  }
}

// Run the test
testApiCall();