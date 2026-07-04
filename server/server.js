const express = require('express');
const cors = require('cors');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

// Submit application
app.post('/apply', (req, res) => {
    const data = req.body;

    let applications = [];
    if (fs.existsSync('data.json')) {
        applications = JSON.parse(fs.readFileSync('data.json'));
    }

    data.id = Date.now();
    applications.push(data);

    fs.writeFileSync('data.json', JSON.stringify(applications, null, 2));

    res.json({ success: true, id: data.id });
});

// Get applications
app.get('/applications', (req, res) => {
    if (fs.existsSync('data.json')) {
        res.json(JSON.parse(fs.readFileSync('data.json')));
    } else {
        res.json([]);
    }
});

const PORT = 3000;
app.listen(PORT, () => console.log("Server running on http://localhost:3000"));