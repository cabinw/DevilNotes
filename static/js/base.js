jQuery(document).ready(function(){
	$(".show a").attr("target", "_blank");
	$(".dsq-widget-meta a").each(function(){
		$(this).attr("href", $(this).attr("href").replace("localhost:8888", "www.rainmoe.com"));
	});
});