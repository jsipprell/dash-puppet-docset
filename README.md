dash-puppet-docset
==================

Dash docset for puppet (2.7.21 only at the moment)

This docset was generated from the [puppet-docs github git repo][2], it only contains reference documentation for puppet
2.7.21 at the moment. See [here][1] for more information on puppet.

This was a fairly fast-paced attempt, at as yet there is no way to automate pulling in the html generated from puppet-docs,
as it embeds a lot of unrelated content (site navigation, etc) into each page. I removed all extraneous content and
paired it down to the fundamentals manually. I also had to make some minor modifications to the css, although I tried to
stay away from anything that was fundamental to the look-and-feel of the reference itself.

Regenerating the docset Index
-----------------------------
The Dash docset sqlite index can be regenerated via:

    $ echo 'delete from searchIndex;' | sqlite3 puppet.docset/Contents/Resources/docSet.dsidx
    $ ./regen-sql-index.sh | sqlite3 puppet.docset/Contents/Resources/docSet.dsidx

Feed
----
A dash installable feed is available here (you'll need to open it inside Dash, I've nowhere to serve a url-encoded
*dash-feed://* url from): https://raw.github.com/jsipprell/dash-puppet-docset/master/puppet.xml

Issues
------
* There isn't always clear mapping between Dash docset "Entry Types" and the elements of the [puppet reference manual][3].
  For example, "Indirections" -- I've set those to Dash's "Interface" type, but that obviously isn't really right.
* The docset index page is set to the puppet types page because it's what I use most, but it would probably be good to pull in
  something more generic/appropriate from puppet-docs.
* Only 2.7.21 docs (really, 2.7."latest") at the moment.
* Automation for pulling in docs from the original puppet markdown or modifying the puppet-docs regen
  is some fashion so that it can generate a docset.
* Figure out how to provide nested references ala some of the other docsets (Python, Apple, etc)

[1]: http://docs.puppetlabs.com/puppet/
[2]: https://github.com/puppetlabs/puppet-docs
[3]: http://docs.puppetlabs.com/puppet/2.7/reference/
