// -------- helper functions & utilities ----------
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}
function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}
function rep(obj, n) {
  return new Array(n).fill(obj);
}
var startTime = (new Date()).getTime();
function time() {
  var now = (new Date()).getTime();
  return now - startTime;
}

var chains = _.shuffle([
  { document: '002', chain: 3 },
  { document: '004', chain: 13 },
  { document: '008', chain: 2 },
  { document: '010', chain: 0 },
  { document: '012', chain: 4 },
  { document: '013', chain: 15 },
  { document: '015', chain: 1 },
  { document: '020', chain: 13 },
  { document: '021', chain: 3 },
  { document: '022', chain: 2 }
]);

// Shows slides. We're using jQuery here - the **$** is the jQuery selector function, which takes as input either a DOM element or a CSS selector string.
function showSlide(id) {
  // Hide all slides
  $(".slide").hide();
  // Show just the slide we want to show
  $("#"+id).show();
}

$(".slide").append('<div class="progress"><span>Progress: </span>' +
    '<div class="bar-wrapper"><div class="bar" width="0%">' +
    '</div></div></div>')

// -------- experiment structure ----------
var experiment = {
  totalNQns: 10 + 4, /*intro, instructions, demographic, debriefing*/
  // log data to send to mturk here
  data: {
    trials: [],
    events: [],
    demographics: [],
    randomSeed: aRandomSeed,
  },
  // store state information here
  state: {
    trialnum: -1,
    next: function() { return experiment.defaultNext() },
    log: function() { return experiment.defaultLog() },
    responseError: function() { return experiment.defaultResponseError() },
  },
  defaultLog: function() {
    return true;
  },
  defaultNext: function() {
    var logSuccess = experiment.state.log();
    if (logSuccess) {
      experiment.state.trialnum++;
      experiment.progress();
      var state = experimentStates.shift();
      experiment[state]();
    } else {
      experiment.state.responseError();
    }
  },
  defaultResponseError: function() {
    $('.err').show();
  },
  progress: function() {
    $('.err').hide();
    var nQns = experiment.state.trialnum;
    $('.bar').css('width', ( (nQns / experiment.totalNQns)*100 + "%"));
  },
  intro: function() {
    showSlide("intro");
    $(".start").click(function() {
      $(this).unbind("click");
      experiment.state.next();
    })
  },
  // first slide (instructions)
  instructions: function() {
    showSlide("instructions");
  },
  // run at start of block
  trial: function() {
    var trialStartTime = time();
    $('.response').remove();
    $('#continue').remove();
    showSlide("trial");
    var chain = chains.shift();
    var nCloze = $('.document' + chain.document + '.chain' + chain.chain + '.cloze').length;
    var clozeIndex = getRandomInt(0, nCloze);
    $('.chain').hide();
    $('.chain.document' + chain.document + '.chain' + chain.chain).show();
    $('.cloze.document' + chain.document + '.chain' + chain.chain).show();
    $('.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).hide();
    var responseInput = $('<input/>', {type: 'text', class: 'response', size: '40'});
    $('.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).before(responseInput);
    experiment.state.log = function() {
      var trialResponseTime = time();
      var response = $('.response').val();
      if (response.length > 0) {
        experiment.data.trials.push({
          document: chain.document,
          chain: chain.chain,
          response: response,
          original: $('.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).html(),
          clozeIndex: clozeIndex,
          clozeHTML: $('.chain.document' + chain.document + '.chain' + chain.chain).html(),
          trialnum: experiment.state.trialnum,
          rt: trialResponseTime - trialStartTime
        })
        return true;
      } else {
        return false;
      }
    }
  },
  demographic: function() {
    $(".languageFree").hide();
    showSlide("demographic");
    $("#language").change(function() {
      if ($("#language").val() == 'eng+other' | $("#language").val() == 'other') {
        $(".languageFree").show();
      } else {
        $(".languageFree").hide();
      }
    })
    experiment.state.log = function() {
      var language = $("#language").val();
      var languageFree = $("#languageFree").val();
      var gender = $("#gender").val();
      var age = $("#age").val();
      var ethnicity = $("#ethnicity").val();
      var education = $("#education").val();
      var studyQuestionGuess = $("#studyQuestionGuess").val();
      var comments = $("#comments").val();
      if (language=='' | gender=='' | education=='') {
        // if blanks, no successful log
        return false;
      } else {
        var demographics = [
          'language', 'languageFree', 'gender', 'age',
          'ethnicity', 'education', 'studyQuestionGuess', 'comments'
        ];
        for (var i=0; i<demographics.length; i++) {
          var demographic = demographics[i];
          experiment.data.demographics.push({
            response: $("#" + demographic).val(),
            qtype: demographic
          })
        }
        return true;
      }
    }
    experiment.state.responseError = function() {
      $(".footnote").css({color: "red"});
      $("#language").click(function() {
        $(".footnote").css({color: "black"});
      })
      $("#gender").click(function() {
        $(".footnote").css({color: "black"});
      })
      $("#education").click(function() {
        $(".footnote").css({color: "black"});
      })
    }
  },
  finished: function() {
    experiment.state.log = experiment.defaultLog();
    clearInterval(mouseLoggerId);
    experiment.data.startTime = startTime;
    experiment.data.seed =  aRandomSeed;
    // Show the finish slide.
    showSlide("finished");
    // Wait 1.5 seconds and then submit the whole experiment object to Mechanical Turk (mmturkey filters out the functions so we know we're just submitting properties [i.e. data])
    setTimeout(function() { turk.submit(experiment.data) }, 1500);
    console.log(JSON.stringify(experiment.data));
  },
  debriefing: function() {
    showSlide("debriefing");
  }
};

// -------- run experiment ----------
var experimentStates = ["intro", "instructions"].concat(
      rep("trial", 10)
    ).concat(["demographic", "debriefing", "finished"]);

$(document).ready(function() {

  // $('.slide').hide(); //hide everything

  //make sure turkers have accepted HIT (or you're not in mturk)
  if (turk.previewMode) {
    $("#mustaccept").show();
  } else {
    experiment.state.next();
  }

  var repeatWorker = false;
  if (repeatWorker) {
    $('.slide').empty();
    alert("You have already completed the maximum number of HITs allowed by this requester. Please click 'Return HIT'.");
  }
})

// -------- record all the events ----------
var x = 0;
var y = 0;

var slideLeftMargin = parseFloat($(".slide").css("margin-left")) +
      parseFloat($(".slide").css("padding-left"))

document.onmousemove = function(e) {
  x = (e.pageX - slideLeftMargin) / $(".slide").width();
  y = e.pageY / $(".slide").height();
};
$(document).click(function(e) {
  experiment.data.events.push({
        type: "click",
        x: x,
        y: y,
        time: time()
  });
});
$(document).keyup(function(e){
  experiment.data.events.push({
        type: "keyup",
        keyCode: e.keyCode,
        key: String.fromCharCode(e.keyCode),
        time: time()
  });
});
var mouseLoggerId;
$(document).ready(function() {
  $(".continue").click(function() {
    $(this).unbind("click");
    this.blur();
    experiment.data.events.push({
          type: "click",
          x: x,
          y: y,
          time: time()
    });
    experiment.next();
  });
  mouseLoggerId = setInterval(function(e) {
    experiment.data.events.push({
          type: "position",
          x: x,
          y: y,
          time: time()
    });
  }, 50);
});
