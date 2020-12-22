// check that jQuery is loaded
if (typeof jQuery != 'undefined') {  
	// jQuery is loaded => print the version
	console.log("jQuery version = " + jQuery.fn.jquery);
} else {
	console.log('jQuery is not loaded!');
}

function get_results_list() {
	return $("#grid-search-results").find("li");
}

function highlight(card,color) {
	card.css("background-color",color)
}

function process_results(results) {
	results.each(function (index) {
		var item = $(this);
		var card = item.find("div.list-card-info");
		highlight(card,"#ff9999");
	});
}

process_results(get_results_list());
