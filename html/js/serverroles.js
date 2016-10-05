function getDocHeight() {
    var D = document;
    return Math.max(
        Math.max(D.body.scrollHeight, D.documentElement.scrollHeight),
        Math.max(D.body.offsetHeight, D.documentElement.offsetHeight),
        Math.max(D.body.clientHeight, D.documentElement.clientHeight)
    );
}

Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

Array.insertAfter = function(obj, firstItem, newItem) {
    for (var i=0; i<obj.length; i++) {
        if (obj[i] == firstItem) {
            obj.splice(i+1,0,newItem);
            return true;
        }
    }
    return;
};

Array.remove = function(obj, item) {
    for (var i=0; i<obj.length; i++) {
        if (obj[i] == item) {
            obj.splice(i,1);
            Array.remove(obj,item);
            return true;
        }
    }
    return;
};
