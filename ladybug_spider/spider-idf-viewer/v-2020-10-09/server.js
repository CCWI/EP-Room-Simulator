const http = require('http');
const fs = require('fs');
const path = require('path');

const port = 50715;
const rootDir = __dirname;

//read file content
function getFileContent(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

//to get MIME-type with file extension
function getMimeType(filePath) {
  const checkMimeType = path.extname(filePath);
  switch (checkMimeType) {
    case '.html': //needed for html (visualisation)
      return 'text/html';
    case '.css':  //needed for menu
      return 'text/css';
    //default MIME-type for other filetypes, otherwise it will risk crashing
    default:
      return 'text/plain';
  }
}

//create http-server
const server = http.createServer((req, res) => {
  const urlPath = req.url === '/' ? '/spider-idf-viewer.html' : req.url;
  const filePath = path.join(rootDir, urlPath);

  //check, if file exists
  if (fs.existsSync(filePath)) {
    //read filecontent
    const fileContent = getFileContent(filePath);
    //get MIME-type with file extension
    const mimeType = getMimeType(filePath);

    //set content-type header
    res.setHeader('Content-Type', mimeType);
    //send file content as response
    res.end(fileContent);
  } else {
    //error if file not found
    res.statusCode = 404;
    res.end('File not found');
  }
});

//start server
server.listen(port, () => {
  console.log(`server running on port ${port}`);
});
