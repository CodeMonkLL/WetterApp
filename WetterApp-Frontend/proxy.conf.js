// Zielhost unterscheidet sich: im Container heißt das Backend "backend", lokal "localhost".
module.exports = {
  "/api": {
    target: process.env["API_URL"] || "http://localhost:5000",
    secure: false,
    changeOrigin: true,
  },
};
