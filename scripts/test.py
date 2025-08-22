import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import asdict

from src.utils import html_to_structured_text_bs4
from src.extractor import LLMBondExtractor

from config import config

text = """
<DOCUMENT>
<TYPE>424B2
<SEQUENCE>1
<FILENAME>d201409d424b2.htm
<DESCRIPTION>424B2
<TEXT>
<HTML><HEAD>
<TITLE>424B2</TITLE>
</HEAD>
 <BODY BGCOLOR="WHITE" STYLE="line-height:Normal">
<h5 align="left" style="font-size:10pt;font-weight:bold"><a href="#toc">Table of Contents</a></h5>


<Center><DIV STYLE="width:8.5in" align="left">
 <P STYLE="margin-top:0pt; margin-bottom:0pt; font-size:10pt; font-family:Times New Roman" ALIGN="right"><B>Filed Pursuant to Rule 424(b)(2) <BR> File No. 333-263244 </B></P>
<p STYLE="margin-top:0pt;margin-bottom:0pt ; font-size:8pt">&nbsp;</P> <P STYLE="margin-top:6pt; margin-bottom:0pt; font-size:10pt; font-family:Times New Roman"><B>PROSPECTUS SUPPLEMENT </B></P>
<P STYLE="margin-top:0pt; margin-bottom:0pt; font-size:10pt; font-family:Times New Roman">(To Prospectus Dated March&nbsp;2, 2022) </P> <P STYLE="font-size:4pt;margin-top:0pt;margin-bottom:0pt">&nbsp;</P>
<P STYLE="font-size:0pt;margin-top:0pt;margin-bottom:0pt">&nbsp;</P> <P STYLE="margin-top:0pt;margin-bottom:0pt" ALIGN="center">


<IMG SRC="g201409g07i16.jpg" ALT="LOGO" STYLE="width:1.83333in;height:0.762582in;">
 </P> <P STYLE="margin-top:6pt; margin-bottom:0pt; font-size:14pt; font-family:Times New Roman" ALIGN="center"><B>$500,000,000 6.950%
<FONT STYLE="white-space:nowrap"><FONT STYLE="white-space:nowrap">Fixed-to-Fixed</FONT></FONT> Reset Rate Junior Subordinated Notes due 2055 </B></P> <P STYLE="font-size:4pt;margin-top:0pt;margin-bottom:0pt">&nbsp;</P><center>
<P STYLE="line-height:6.0pt;margin-top:0pt;margin-bottom:2pt;border-bottom:1.00pt solid #000000;width:21%">&nbsp;</P></center> <P STYLE="margin-top:4pt; margin-bottom:0pt; text-indent:4%; font-size:9pt; font-family:Times New Roman">We are offering
$500,000,000 aggregate principal amount of 6.950% <FONT STYLE="white-space:nowrap"><FONT STYLE="white-space:nowrap">Fixed-to-Fixed</FONT></FONT> Reset Rate Junior Subordinated Notes due 2055 (the &#147;notes&#148;). The notes will bear interest
(i)&nbsp;from and including the original issue date (as defined herein) to, but excluding, July&nbsp;15, 2030 at the rate of 6.950% per annum and (ii)&nbsp;from and including July&nbsp;15, 2030, during each Reset Period (as defined herein) at a rate
per annum equal to the Five-year U.S. Treasury Rate (as defined herein) as of the most recent Reset Interest Determination Date (as defined herein) plus a spread of 2.890%, to be reset on each Reset Date (as defined herein). The notes will mature on
July&nbsp;15, 2055. Interest on the notes will accrue from and including December 6, 2024 and will be payable semi-annually in arrears on January&nbsp;15 and July&nbsp;15 of each year, beginning on July&nbsp;15, 2025. </P>
<P STYLE="margin-top:4pt; margin-bottom:0pt; text-indent:4%; font-size:9pt; font-family:Times New Roman">So long as no Event of Default (as defined herein) with respect to the notes has occurred and is continuing, we may, at our option, defer
interest payments on notes, from time to time, for one or more deferral periods of up to 20 consecutive semi-annual Interest Payment Periods (as defined herein). During any deferral period, interest on the notes will continue to accrue at the
then-applicable interest rate on the notes (as reset from time to time on any Reset Date occurring during such deferral period in accordance with the terms of the notes) and, in addition interest on deferred interest will accrue at the
then-applicable interest rate on the notes (as reset from time to time on any Reset Date occurring during such deferral period in accordance with the terms of the notes), compounded semi-annually, to the extent permitted by applicable law. See
&#147;Description of the Notes&#151;Option to Defer Interest Payments.&#148; </P> <P STYLE="margin-top:4pt; margin-bottom:0pt; text-indent:4%; font-size:9pt; font-family:Times New Roman">At our option, we may redeem notes at the times and at the
applicable redemption prices described in this prospectus supplement. The notes will be our unsecured obligations and will rank junior and subordinate in right of payment to the prior payment in full of our existing and future Senior Indebtedness
(as defined herein). The notes will rank equally in right of payment with our existing $950&nbsp;million aggregate principal amount of 7.600% <FONT STYLE="white-space:nowrap"><FONT STYLE="white-space:nowrap">Fixed-to-Fixed</FONT></FONT> Reset Rate
Junior Subordinated Notes due 2055 and with any future unsecured indebtedness that we may incur from time to time if the terms of such indebtedness provide that it ranks equally with the notes in right of payment. None of our subsidiaries will
guarantee the notes. The notes will be issued only in registered form in minimum denominations of $2,000 and integral multiples of $1,000 in excess thereof. </P>
<P STYLE="margin-top:4pt; margin-bottom:0pt; text-indent:4%; font-size:9pt; font-family:Times New Roman">The notes are a new issue of securities with no established trading market. We do not intend to apply for the listing or trading of the notes on
any securities exchange of trading facility or for inclusion of the notes in any automated quotation system. </P> <P STYLE="font-size:4pt;margin-top:0pt;margin-bottom:0pt">&nbsp;</P><center>
<P STYLE="line-height:6.0pt;margin-top:0pt;margin-bottom:2pt;border-bottom:1.00pt solid #000000;width:21%">&nbsp;</P></center> <P STYLE="margin-top:4pt; margin-bottom:0pt; text-indent:5%; font-size:11pt; font-family:Times New Roman"><B>Investing in
the notes involves risks that are described in the &#147;<A HREF="#supptoc201409_8">Risk Factors</A>&#148; section beginning on page <FONT STYLE="white-space:nowrap">S-13</FONT> of this prospectus supplement. </B></P>
<P STYLE="font-size:4pt;margin-top:0pt;margin-bottom:0pt">&nbsp;</P>
<TABLE CELLSPACING="0" CELLPADDING="0" WIDTH="84%" BORDER="0" STYLE="BORDER-COLLAPSE:COLLAPSE; font-family:Times New Roman; font-size:9pt" ALIGN="center">
"""

text = html_to_structured_text_bs4(text)
print(text)

bondex = LLMBondExtractor(config['gemini']['api_key'], config['gemini']['model'])
bonds = bondex.extract_bonds_from_text(text, '424B2')
print(bonds[0])