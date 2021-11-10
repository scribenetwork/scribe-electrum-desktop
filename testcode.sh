#!/bin/bash
grep -rI "electrum\/" ../electrum-scribe . 2> /dev/null | grep -v -e "\/locale\/" -e "README" -e "RELEASE-NOTES" -e "electrum\/{version\.ELECTRUM\_VERSION}" -e "\/issues\/4994" -e "\/issues\/5032"
grep -rI "import\ electrum " ../electrum-scribe . 2> /dev/null | grep -v -e "\/locale\/" -e "README" -e "RELEASE-NOTES" -e "electrum\/{version\.ELECTRUM\_VERSION}" -e "\/issues\/4994" -e "\/issues\/5032"
grep -rI "import\ electrum\." ../electrum-scribe . 2> /dev/null | grep -v -e "\/locale\/" -e "README" -e "RELEASE-NOTES" -e "electrum\/{version\.ELECTRUM\_VERSION}" -e "\/issues\/4994" -e "\/issues\/5032"
grep -rI "from\ electrum " ../electrum-scribe . 2> /dev/null | grep -v -e "\/locale\/" -e "README" -e "RELEASE-NOTES" -e "electrum\/{version\.ELECTRUM\_VERSION}" -e "\/issues\/4994" -e "\/issues\/5032"
grep -rI "from\ electrum\." ../electrum-scribe . 2> /dev/null | grep -v -e "\/locale\/" -e "README" -e "RELEASE-NOTES" -e "electrum\/{version\.ELECTRUM\_VERSION}" -e "\/issues\/4994" -e "\/issues\/5032"
grep -rI "electrum\.gui" ../electrum-scribe . 2> /dev/null | grep -v -e "\/locale\/" -e "README" -e "RELEASE-NOTES" -e "electrum\/{version\.ELECTRUM\_VERSION}" -e "\/issues\/4994" -e "\/issues\/5032"
pytest electrum_scribe/tests/ --full-trace
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
