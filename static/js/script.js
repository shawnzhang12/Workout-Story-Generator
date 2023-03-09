var csrf_token = "{{ csrf_token() }}";

$(document).ready(function() {
  // Function to send AJAX request to server with modified exercise data
  
  function updateExercise(id, name, reps, sets) {
    console.log(id);
    console.log(name);
    console.log(reps);
    console.log(sets);
    $.ajax({
      type: 'POST',
      url: '/update',
      dataType: 'json',
      contentType: 'application/json',
      headers: {"X-CSRFToken" : csrf_token},
      data: JSON.stringify({
        id: id,
        name: name,
        reps: reps,
        sets: sets
      }),
      
      success: function(response) {
        console.log(response);
      },
      error: function(error) {
        console.log(error);
      }
    });
  }

  // Function to send AJAX request to server to delete exercise data
  function deleteExercise(id) {
    console.log(id);
    $.ajax({
      type: 'POST',
      url: '/delete',
      dataType: 'json',
      contentType: 'application/json',
      headers: {"X-CSRFToken" : csrf_token},
      data: JSON.stringify({
        id: id
      }),
      success: function(response) {
        console.log(response);
      },
      error: function(error) {
        console.log(error);
      }
    });
  }

  // Function to send AJAX request to server to add default row
  function addExercise(name, reps, sets) {
    console.log(name);
    console.log(reps);
    console.log(sets);
    $.ajax({
      type: 'POST',
      url: '/add',
      dataType: 'json',
      contentType: 'application/json',
      headers: {"X-CSRFToken" : csrf_token},
      data: JSON.stringify({
        name: name,
        reps: reps,
        sets: sets
      }),
      success: function(response) {
        console.log(response);
      },
      error: function(error) {
        console.log(error);
      }
    });
  }


  // Click handler for edit button
  $(document).on('click', '.edit', function() {
    // Change table cell content to input fields
    $(this).parent().siblings('td.data').each(function() {
      var content = $(this).html();
      $(this).html('<input class="table-input" value="' + content + '" />');
    });

    // Show save button, hide edit and delete buttons
    $(this).siblings('.save').show();
    $(this).siblings('.delete').hide();
    $(this).hide();
  });

  // Click handler for save button
  $(document).on('click', '.save', function() {
    // Get exercise data from input fields
    var id = $(this).parents('tr').data('id');
    var name = $(this).parent().siblings('td.data').eq(0).children('input').val();
    var reps = $(this).parent().siblings('td.data').eq(1).children('input').val();
    var sets = $(this).parent().siblings('td.data').eq(2).children('input').val();

    // Update table cell content with exercise data
    $(this).parent().siblings('td.data').each(function() {
      var content = $(this).children('input').val();
      $(this).html(content);
    });

    // Show edit and delete buttons, hide save button
    $(this).siblings('.edit').show();
    $(this).siblings('.delete').show();
    $(this).hide();

    // Update exercise data on server
    updateExercise(id, name, reps, sets);
  });

  // Click handler for delete button
  $(document).on('click', '.delete', function() {
    // Get exercise id and delete row from table
    var id = $(this).parents('tr').data('id');
    $(this).parents('tr').remove();

    // Delete exercise data on server
    deleteExercise(id);
  });

  // Click handler for add button
  $(document).on('click', '.add', function() {
    // Add new row to table
    var newID = $('table tr').length
    var newRow = '<tr data-id="' + newID + '"><td class="data"></td><td class="data"></td><td class="data"></td><td><button class="save">Save</button><button class="edit">Edit</button><button class="delete">Delete</button></td></tr>';
    $(this).parents('table').append(newRow);

    addExercise('Null', 'Null', 'Null');
  });
});