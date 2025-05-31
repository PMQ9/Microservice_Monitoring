const http = require('http');

const frontendUrl = process.argv[2] || 'http://localhost:30001';

function sendRequest() {
  http.get(frontendUrl, (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => console.log('Response:', data));
  }).on('error', (e) => console.error('Error:', e.message));
}

for (let i = 0; i < 10; i++) {
  setTimeout(sendRequest, i * 1000);
}