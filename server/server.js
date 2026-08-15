const express = require('express');
const path = require('path');
const app = express();
const { callPdb } = require('./dbClient');

app.use(express.json());

app.use(express.static(path.join(__dirname, '../public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/landing/index.html'));
});

app.get('/api/get-all', async (req, res) => {
    const response = await callPdb('/get-all', 'GET');
    res.json({ users: response.res });
});

app.listen(3000, () => console.log('server running on http://localhost:3000'));