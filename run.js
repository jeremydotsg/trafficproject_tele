var page = require('webpage').create();

//page.onError = function(msg, trace) {
    // Suppress errors
//};

page.open('https://www.cimbclicks.com.sg/sgd-to-myr', function(status) {
    if (status === 'success') {
        console.log('Page loaded successfully');
        setTimeout(function() {
            console.log('Waited for 5 seconds');
            page.render('example.png');
            phantom.exit();
        }, 5000); // Wait for 5000 milliseconds (5 seconds)
    } else {
        console.log('Failed to load the page');
        phantom.exit();
    }
});
