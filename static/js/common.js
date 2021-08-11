/**
 * 点击画布的时候隐藏右键菜单
 */
$('.container').click(function(){
    hideMenu();
});

$("#hide").click(function(){
        console.log('hide_params:',data_tmp)
        hide(data_tmp);
        hideMenu();
});

$("#expand").click( function(){
    console.log('expand_params:',data_tmp)
    expand(data_tmp);
    hideMenu();
});

$("#collapse").click(function(){
    console.log('collapse_params:',data_tmp)
    collapse(data_tmp);
    hideMenu();
});

$("#mark_none").click(function(){
    mark_color(data_tmp, colors.none);
    hideMenu();
});

$("#mark_red").click(function(){
    mark_color(data_tmp, colors.red);
    hideMenu();
});

$("#mark_yellow").click(function(){
    mark_color(data_tmp, colors.yellow);
    hideMenu();
});

$("#mark_green").click(function(){
    mark_color(data_tmp, colors.green);
    hideMenu();
});

function mark_color(root, color){
    var option = myChart.getOption();
    var nodes = data;
    var links = link;

    var mark = [root];
    while (mark.length > 0) {
        var current = mark.pop();
        dyeNode(current.id, color);
        for (var i = 0; i < links.length; i++) {
            if (links[i].source === current.id) {
                var targetNode = findNodeById(links[i].target, nodes);
                if (targetNode.store > current.store) {
                    mark.push(targetNode);
                }
            }
        }
    }
}

function dyeNode(id, color){
    var option = myChart.getOption();
    for(var i=0, len=option.series[0].nodes.length; i<len; i++){
        //console.log(option.series[0].nodes[i].name + ":" + name);
        if(id === option.series[0].nodes[i].id){
            option.series[0].nodes[i].itemStyle.color = color;
        }
    }
    myChart.setOption(option);
}

function hideMenu(){
    $('#right-box').css({
        'display': 'none',
        'left': '-9999px',
        'top': '-9999px'
    });
}

function hide(root){
    var option = myChart.getOption();
    var nodes = data;
    var links = link;

    var mark = [root];
    while(mark.length > 0){
        var current = mark.pop();
        hideNode(current.id);
        for(var i=0; i<links.length; i++){
            if(links[i].source === current.id){
                targetNode = findNodeById(links[i].target, nodes);
                if(targetNode.store > current.store){
                    mark.push(targetNode);
                }
            }
        }
    }
}

function findNodeById(id, nodes){
    for(var i=0; i<nodes.length; i++){
        if(nodes[i].id === id){
            return nodes[i];
        }
    }
    return null;
}

function hideNode(id){
    var option = myChart.getOption();
    for(var i=0, len=option.series[0].nodes.length; i<len; i++){
        //console.log(option.series[0].nodes[i].name + ":" + name);
        if(id === option.series[0].nodes[i].id){
            option.series[0].nodes[i].category = -1;
        }
    }
    myChart.setOption(option);
}

function showNode(id){
    var option = myChart.getOption();
    console.log(option.series[0].nodes[i]);
    for(var i=0, len=option.series[0].nodes.length; i<len; i++){
        //console.log(option.series[0].nodes[i].name + ":" + name);
        if(id === option.series[0].nodes[i].id){
            option.series[0].nodes[i].category = option.series[0].nodes[i].store;
        }
    }
    myChart.setOption(option);
}

function collapse(root) {
    var option = myChart.getOption();
    var nodes = data;
    var links = link;

    var mark = [root];
    while(mark.length > 0){
        var current = mark.pop();
        if(current.id !== root.id){
            hideNode(current.id);
        }
        for(var i=0; i<links.length; i++){
            if(links[i].source === current.id){
                targetNode = findNodeById(links[i].target, nodes);
                if(targetNode.store > current.store){
                    mark.push(targetNode);
                    //console.log(mark);
                }
            }
        }
    }
}

function expand(root) {
    var nodes = data;
    var links = link;
   // var root = params.data;

    //console.log(params);

    for(var i=0; i<links.length; i++){
        if(links[i].source == root.id){
            console.log("expand:source="+links[i].source+" root="+root.id);
            targetNode = findNodeById(links[i].target, nodes);
            console.log("targetNode.store:"+targetNode.store+"root.store:"+root.store);
            if(targetNode.store > root.store){
                showNode(targetNode.id);
            }
        }
    }
}
