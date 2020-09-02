//handle project archiving
function projectArchive() {
    //$.ajax(pid + '/api/archive').done(function (res) {
            //console.log(res);
    //});
    // jQuery hack to download server returned file to client
    $('#archiveForm').attr({ action: pid + '/api/archive' });
    $('#archiveForm').submit();
    return false;
    };

function projectArchiveDelete() {
    //$.ajax(pid + '/api/archive').done(function (res) {
            //console.log(res);
    //});
    // jQuery hack to download server returned file to client
    $('#archiveDeleteForm').attr({ action: pid + '/api/archive' });
    var input = $("<input>")
               .attr("type", "hidden")
               .attr("name", "delete").val("true");
    $('#archiveDeleteForm').append($(input));
    $('#archiveDeleteForm').submit();
    return false;
    };

    // example code that lists all selected file in the input box, modify later
    // We can attach the `fileselect` event to all file inputs on the page
    $(document).on('change', ':file', function() {
        var input = $(this),
        numFiles = input.get(0).files ? input.get(0).files.length : 1,
        label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
        input.trigger('fileselect', [numFiles, label]);
    });