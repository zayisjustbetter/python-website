const express = require('express');
const bodyParser = require('body-parser');
const fetch = require('node-fetch'); // or global fetch in newer Node

const app = express();
app.use(bodyParser.urlencoded({ extended: true }));

app.post('/submit-form', async (req, res) => {
    const token = req.body['h-captcha-response'];
    const secretKey = 'ES_8582c9b4f8724ba086eb7e68af308e97';

    if (!token) {
        return res.status(400).send('Please complete the captcha.');
    }

    const verifyUrl = `https://hcaptcha.com`;
    const params = new URLSearchParams({
        secret: secretKey,
        response: token
    });

    try {
        const response = await fetch(verifyUrl, {
            method: 'POST',
            body: params
        });
        const data = await response.json();

        if (data.success) {
            // Captcha passed successfully, process form data here
            res.send('Form submitted successfully!');
        } else {
            // Verification failed
            res.status(403).send('Captcha verification failed.');
        }
    } catch (error) {
        res.status(500).send('Server error during captcha verification.');
    }
});

app.listen(3000, () => console.log('Server running on port 3000'));
