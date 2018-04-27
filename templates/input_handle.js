/**
 * Created by zhaoxin on 18/04/27.
 */
function readJSONFile(file) {
    var rawFile = new XMLHttpRequest();
    rawFile.open('GET', file, false);
    rawFile.onreadystatechange = function() {
        if(rawFile.readyState == 4) {
            if(rawFile.status === 200 || rawFile.status == 0) {
                var allText = rawFile.responseText;
                //convert to JSON object
                var JSONText = JSON.parse(allText);
            }
        }
    }
    console.log(JSONText);

}
window.onload = document.getElementById('submitURL').addEventListener('click', function() {
    var inputURL = document.getElementById('profilingURL').value;
    console.log(inputURL);
    $.post('receiver', inputURL, function() {});
    event.preventDefault();
    // Use AJAX to send data to the server
    // alert(inputURL);
});