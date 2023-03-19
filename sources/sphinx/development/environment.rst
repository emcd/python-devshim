.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+

.. include:: <isopub.txt>

*******************************************************************************
Environment and Utilities
*******************************************************************************

The development environment is prepared and utilized via the ``develop.py``
program distributed with the project sources. This program is built against the
Python standard library and has no third-party dependencies. It can locally
bootstrap Python implementations and Python packages in a manner that does not
intrude with either a system-wide or user-specific Python installation. Aside
from a working Python of the minimum required version and a sane standard
library distribution with that Python, there are no requirements which must be
installed prior to development on the project.

There is a possible exception to the foregoing statement. If a Python
implementation, which is specified for project development, requires
compilation from sources, then you should ensure that appropriate C header
files are installed for successful compilation of the interpreter and relevant
standard library modules. The suggested build environment section of the `Pyenv
Wiki <https://github.com/pyenv/pyenv/wiki>`_ wiki has instructions for
installing the relevant dependencies for various operating systems and package
managers.

You can bootstrap the project development environment with the following
command or similar, depending on your Python installation::

    python3 develop.py bootstrap

While you can write ``python3 develop.py`` for each task invocation, there
exists a shortcut for popular shells:

.. tab:: bash

    .. code-block:: sh

        eval "$(python3 develop.py ease --with-completions)"

By default, this will create a shell function, called ``devshim``, which you
can use as a command instead of ``python3 develop.py``.

Commit Signatures
===============================================================================

All commits to the project must be signed with a valid GPG/PGP or S/MIME secret
key. You can use `GNU Privacy Guard <https://gnupg.org/>`_ or a similar tool to
generate a signing key if you do not already have one. And, you can likewise
use such a tool to sign your commits. Github has a good guide on the following
topics:

* `Commit Signature Verification
  <https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification>`_
* `GPG Key Generation
  <https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key>`_
* `GPG Key Registration on Github
  <https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account>`_
* `Git Client Configuration for Commit Signatures
  <https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key>`_

If you do not wish to expose a personal email address in association with a
signing key, you can use the `no-reply email address
<https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address>`_
associated with your Github account instead.

In addition to registering the signature verification public key, which
corresponds to your secret signing key, with Github, you may also publish the
signature verification public key to well-known public key servers, such as:

* `OpenPGP Keyserver <https://keys.openpgp.org/>`_
* `Ubuntu Keyserver <https://keyserver.ubuntu.com/>`_

`EditorConfig <https://editorconfig.org>`_
===============================================================================

Most modern code editors support per-file type configuration via EditorConfig_.
This ensures that project standards for things, such as maximum line length,
trailing whitespace, and indentation are enforced without the need
for lots of editor-specific configurations to be distributed with the project.
We recommend that you install an EditorConfig plugin for your editor of choice,
if necessary. We provide an :file:`.editorconfig` file at the top level
of the project repository; this file has configurations relevant
to the project.

`pre-commit <https://pre-commit.com>`_
===============================================================================

As part of the development environment that we provide via Pipenv, there is the
pre-commit_ command. Among other things, this allows you to install Git
pre-commit hooks which will perform additional checks, such as TOML and YAML
linting, before recording a new commit. These hooks will be installed if you
ran ``python3 develop.py bootstrap``. To update them at a later time you can
run::

    devshim freshen-git-hooks install-git-hooks
