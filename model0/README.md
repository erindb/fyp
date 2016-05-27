# Models of storytelling

## Question

How do people generate stories from events?

## Generative Model of Event Sequences

Let's assume we have a generative model of typical event sequences for a domain. This is like a probabilistic version of a "script". We won't try to combine scripts or account for deviations from a script, we'll just assume that the things we want to tell stories about can be generated entirely by one of our scripts. I'll hand-write some of these generative models:

* playing a video game
	- where every time you lose, you go back to level 1
	- the player gets more and more bored with the game the more they play it
	- eventually the player stops playing, either because they get too bored and or because they've won the game
* knitting a scarf
	- sequences of steps
	- occasionally there's a mistake and you have to backtrack
* baking
	- multiple acceptable orders of some things
* routes to get to school
	- branching sequence

We'll sample event chains from this generative model. We'll consider that to be what happened actually.

## Storytelling

* Basic Storyteller

	Basic storyteller can say any subsequence of the actual events, in the order that they occurred.

* Informative Storyteller

	Informative storytellers will try to tell stories that are relatively short but that result in the listener believing what happened is what actually happened.

* Unordered Informative Storyteller

	Unordered informative storyteller doesn't care if the exact sequence is preserved, but it does care that the exact set of events that occurred is preserved in the listener's interpretation.

	That is, if the listener things someone ordered food and then sat down, but in the actual event sequence someone sat down and then ordered food, the *unordered* informative storyteller would have succeeded.

## Future questions

If we know how people's choices of what events to mention
is biased, can we interpret their stories better?

What if a storyteller can use discourse connectives: 'but', 'and', 'so', 'because'?
* When should it mention an event at all?
* When should it mention an event *and* use a modifier?

A thought: I like to think of explanations as stories whose
conclusion is the thing you want to explain.
So understanding the kinds of informativity constraints
on what should go into a story could help understand a bit
more about how explanations work...? And vice versa?