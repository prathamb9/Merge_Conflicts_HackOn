export default async function handler(req, res) {
  // Route to the live AWS backend
  const targetUrl = 'http://amazon-now1.ap-south-1.elasticbeanstalk.com' + req.url;

  try {
    const fetchOptions = {
      method: req.method,
      headers: {
        'Content-Type': req.headers['content-type'] || 'application/json',
      }
    };
    
    // Forward the authorization token if it exists
    if (req.headers['authorization']) {
      fetchOptions.headers['Authorization'] = req.headers['authorization'];
    }

    // Forward the body for POST/PUT requests
    if (req.method !== 'GET' && req.method !== 'HEAD' && req.body) {
      fetchOptions.body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
    }

    // Call the AWS backend
    const response = await fetch(targetUrl, fetchOptions);
    const text = await response.text();
    
    let data;
    try { 
      data = JSON.parse(text); 
    } catch { 
      data = { detail: text }; 
    }

    // Send the response back to the frontend
    res.status(response.status).json(data);
  } catch (error) {
    res.status(500).json({ detail: "Vercel Proxy Error: " + error.message });
  }
}
