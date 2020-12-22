// check that jQuery is loaded
if (typeof jQuery != 'undefined') {  
	// jQuery is loaded => print the version
	console.log("jQuery version = " + jQuery.fn.jquery);
} else {
	console.log('jQuery is not loaded!');
}

function get_results_list() {
	return $("#grid-search-results").find("ul.photo-cards").find("li");
}

function highlight(card,color) {
	card.css("background-color",color)
}

function get_result_zpid(result_li) {
	var id = result_li.find("article").attr("id");
	if (id == undefined) {
		return undefined
	}
	return id
}

function process_results(results) {
	results.each(function (index) {
		var result_li = $(this);
		var zpid = get_result_zpid(result_li);
		var card = result_li.find("div.list-card-info");
		highlight(card,"#ff9999");
	});
}

function on_results_list_changed() {
	var results = get_results_list();
	process_results(results);
}

$('#grid-search-results').on(
	'DOMSubtreeModified',
	'ul.photo-cards',
	on_results_list_changed
);
