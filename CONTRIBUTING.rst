.. highlight:: shell

============
Contributing
============

* Pull Requests Welcome
    * use a feature or fix branch: `feature/<name>` or  `fix/<name>`
    * squash commits
    * write a good commit message https://chris.beams.io/posts/git-commit/
    * Add your name to CONTRIBUTING.rst

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/brettswift/cumulus/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `cumulus` for local development.

1. Fork the `cumulus` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/cumulus.git

3. Install your local copy into a virtualenv. Assuming virtualenv and pyenv are installed,

    $ pyenv virtualenv 3.6 cumulus36
    $ pyenv local cumulus36
    $ cd cumulus/
    $ python setup.py develop (sometimes I use `pip install -e .`)

4. Create a branch, and code.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 cumulus tests
    $ python setup.py test or py.test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Squash changes to a single commit and write a good commit message

    * A good commit message follows: https://chris.beams.io/posts/git-commit/

    $ git fetch --all
    $ git rebase -i [brettswift]/master
    $ # use interactive squash to squash all commits (tip: keep the top one, type `s` or `squash` next to all the others

7. Push code and Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 2.7, 3.4, 3.5 and 3.6, and for PyPy. Check
   https://travis-ci.org/brettswift/cumulus/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

$ py.test tests.test_cumulus


Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then run::

$ bumpversion patch # possible: major / minor / patch
$ git push
$ git push --tags

Travis will then deploy to PyPI if tests pass.
