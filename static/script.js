var CONTENT = [ 
	"My", 
	"Your", 
	"Our", 
	"Everybodys"
];

var PART = 0;
var PARTINDEX = 0;
var INTERVALVAL;
var ELEMENT = document.querySelector("#text");
var CURSOR = document.querySelector("#cursor");

function Type() { 
	var text =  CONTENT[PART].substring(0, PARTINDEX + 1);
	ELEMENT.innerHTML = text;
	PARTINDEX++;

	if(text === CONTENT[PART]) {
		CURSOR.style.display = 'none';

		clearInterval(INTERVALVAL);
		setTimeout(function() {
			INTERVALVAL = setInterval(Delete, 50);
		}, 1000);
	}
}

function Delete() {
	var text =  CONTENT[PART].substring(0, PARTINDEX - 1);
	ELEMENT.innerHTML = text;
	PARTINDEX--;

	if(text === '') {
		clearInterval(INTERVALVAL);

		if(PART == (CONTENT.length - 1))
			PART = 0;
		else
			PART++;
		
		PARTINDEX = 0;

		setTimeout(function() {
			CURSOR.style.display = 'inline-block';
			INTERVALVAL = setInterval(Type, 100);
		}, 200);
	}
}

INTERVALVAL = setInterval(Type, 100);