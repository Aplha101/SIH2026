async function callPdb(endpoint, method = 'GET', bodyData = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (bodyData) {
    options.body = JSON.stringify(bodyData);
  }

  try {
    const response = await fetch(`http://127.0.0.1:5000${endpoint}`, options);
    return await response.json();
  } catch (err) {
    console.error("Error connecting to Python service:", err.message);
    return { success: false, res: [] };
  }
}


    
module.exports = { callPdb };