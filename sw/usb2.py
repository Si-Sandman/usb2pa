#!/usr/bin/env python

from __future__ import print_function
import re
import sys

def printf( str, *args):
    print( str % args, end='' )

# -------------------------------------------------------------------------------- 

class CRC( object ):
    """Class for USB Cyclical Redundancy Check Calculations"""
    debug_print = False

    def _xor( self, a, b ):
        y = []
        for index in range( len(a) ):
            if( a[index] != b[index] ):
                y.append(1)
            else:
                y.append(0)
        if( self.debug_print ):
            printf( 'xor( %s, %s ) = %s  ' % (a,b,y) )
        return y

    def _shift( self, l ):
        firstval = l[0]
        l[0:1] = []             # Delete element 0 (ie: insert/replace elements starting at position 0 up-to-but-not-including 1, with an empty list)
        return firstval

    def _unshift( self, l, newitem ):
        l[:0] = [newitem]       # insert at front

    def _pop( self, l ):
        lastval = l[-1]         # last item in the array
        l[:] = l[:-1]           # Delete last item
        return lastval

    def _push( self, l, newitem ):
        l[:] = l + [newitem]    # insert at end

    def _calc_crcX( self, bitstream, polynomial, crc_reg_start ):
        data    = list( bitstream )
        G       = polynomial
        crc_reg = list( crc_reg_start )

        i = 0
        while( len(data) > 0 ):
            i += 1
            next_data_bit = self._shift( data )

            if( self.debug_print ):
                printf( 'i=%2d : next_data_bit=%s  crc_reg=%s  ' % (i, next_data_bit, crc_reg) )

            next_crc_bit = self._shift( crc_reg )
            if( self.debug_print ):
                printf( 'next_crc_bit=%s  ' % (next_crc_bit) )
                printf( 'crc_reg_postshift=%s  ' % crc_reg )

            self._push( crc_reg, 0 )
            if( self.debug_print ):
                printf( 'crc_reg_postpush=%s  ' % crc_reg )

            if( int(next_data_bit) != int(next_crc_bit) ):
                crc_reg = self._xor( G, crc_reg )
                if( self.debug_print ):
                    printf( 'crc_reg_postxor=%s  ' % (crc_reg) )

            if( self.debug_print ):
                printf( '\n' )

        # invert shift reg contents to generate crc field
        for index, item in enumerate( crc_reg ):
            if( item == 1 ):
                crc_reg[index] = 0
            else:
                crc_reg[index] = 1

        if( self.debug_print ):
            printf( '%s -> %s\n' % (bstr, crc_reg) )
        return crc_reg

    def calc_crc16( self, bitstream ):
        """ calc_crc16 takes a list of ints of value 0 or 1, calculates the USB CRC16 value, 
            and returns the crc value as a list of 16 ints with values of value 0 or 1. """
        # Spec USB2 section 8.3.5.0 & 8.3.5.1
        crc16 = self._calc_crcX( bitstream, 
                polynomial    = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                crc_reg_start = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] )
        return crc16

    def calc_crc5( self, bitstream ):
        """ calc_crc5 takes a list of ints of value 0 or 1, calculates the USB CRC5 value, 
            and returns the crc value as a list of 5 ints with values of value 0 or 1. """
        # Spec USB2 section 8.3.5.0 & 8.3.5.1
        crc5 = self._calc_crcX( bitstream, [0, 0, 1, 0, 1], [1, 1, 1, 1, 1] )
        return crc5

# -------------------------------------------------------------------------------- 

class Packet( object ):
    'USB2 Packet Class'
    tot_pkts        = 0             # Class var
    pkt_num         = 0             # Member var
    raw_byte_list   = []
    pkt_type        = ''

    def _decodePkt( self ):         # Abstract method
        raise NotImplementedError( 'Subclass must implement abstract method' )
    def __init__( self, pkt_data ):
        Packet.tot_pkts += 1        # Class var
        self.pkt_num    += 1        # Member var
        self.raw_byte_list = pkt_data
        self._decodePkt()
    def __repr__( self ):
        return 'Pkt #%d : raw_byte_list=%s' % (self.pkt_num, self.raw_byte_list)
    def print_raw( self ):
        print( "raw %s pkt: " + str( self.pkt_type, self.raw_byte_list ) )
    def print_formatted( self ):
        print( "%-5d : %-10s : %s" % (self.pkt_num, self.pkt_type, str(self.raw_byte_list) ) )

class OutPacket( Packet ):
    'USB2 OUT packet class - a child of the packet class'
    pkt_type    = 'OUT'
    def __init__( self, pkt_data ):
        super( OutPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

        
class InPacket( Packet ):
    'USB2 IN packet class - a child of the packet class'
    pkt_type    = 'IN'
    def __init__( self, pkt_data ):
        super( InPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class SofPacket( Packet ):
    'USB2 SOF packet class - a child of the packet class'
    pkt_type    = 'SOF'
    def __init__( self, pkt_data ):
        super( SofPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class SetupPacket( Packet ):
    'USB2 SETUP packet class - a child of the packet class'
    pkt_type    = 'SETUP'
    pkt_binary  = ''
    addr        = ''
    endpt       = ''
    crc5        = ''
    def __init__( self, pkt_data ):
        super( SetupPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        ## Chap 8.4.1
        #
        # Note, every byte of the pkt is bit-reversed.  However, it is convenient to NOT bit-reverse
        # the PID and then just use a lookup table that has all entries already bit-reversed.  The reason
        # is convenient has to do with the importance of recognizing the PID on a logic-analyzer or simulation
        # of the UTMI interface.  When you see a the first byte on the UTMI bus in simulation or on a logic
        # analyzer, it will be bit-reversed and rather than doing the mental bit-reversal, it's easier to
        # just remember the reversed PID codes.

        # First, bit reverse each byte:
        #       byte0[7:0] <= byte0[0:7]
        #       byte1[7:0] <= byte1[0:7]
        #       byte2[7:0] <= byte2[0:7]
        #
        # Then, concatenating the byte stream from the UTMI i/f into a 24bit word:
        #       word[23:0] = {byte0[7:0], byte1[7:0], byte2[7:0]}
        #
        # Then decode as: bit-reversed again but within the fields:
        #       8 bits : [23:16] -> [16:23] : PID
        #       7 bits : [15:9]  -> [9:15]  : ADDR
        #       4 bits : [8:5]   -> [5:8]   : ENDP
        #       5 bits : [4:0]   -> [0:4]   : CRC5
        #
        # Example SETUP pkt sequence from UTMI of:  
        #       2D 01 E8
        # is:
        #
        #              | 2222 1111  1111 11
        #         bits | 3210 9876  5432 1098 7654 3210
        #       -------| ---- ----  ---- ---- ---- ----
        #       binary = 0010 1101  0000 0001 1110 1000
        #
        # First, bit reverse each byte:
        #       byte0[7:0] <= byte0[0:7]
        #       byte1[7:0] <= byte1[0:7]
        #       byte2[7:0] <= byte2[0:7]
        #
        # (after bit reversal) becomes:
        #

        #                             11 1111 1111 2222
        #                0123 4567  8901 2345 6789 0123

        #              | 2222 1111  1111 11
        #         bits | 3210 9876  5432 1098 7654 3210
        #       -------| ---- ----  ---- ---- ---- ----
        #       binary = 1011 0100  1000 0000 0001 0111
        #                <-------|         |    |     |
        #                   pid     <------|    |     |
        #                             addr  <---|     |
        #                                     ep <----|
        #                                          crc
        # Read each field right to left:                                       
        #
        #   PID     = [16:23] = 0010_1101 = SETUP (0x2D)
        #   ADDR    = [9:15]  =  000_0001 = Addr0
        #   ENDP    = [5:8]   =      0000 = EP15
        #   CRC5    = [0:4]   =    1_1101 = CRC   (0x1D)
        #print "raw_byte_list:%s" % self.raw_byte_list
        reversed_raw_byte_list = []
        reversed_raw_byte_list.append( "{0:08b}".format(int(self.raw_byte_list[0],16))[::-1] ) # zero pad, then bit reversal
        reversed_raw_byte_list.append( "{0:08b}".format(int(self.raw_byte_list[1],16))[::-1] ) # zero pad, then bit reversal
        reversed_raw_byte_list.append( "{0:08b}".format(int(self.raw_byte_list[2],16))[::-1] ) # zero pad, then bit reversal
        self.pkt_binary = reversed_raw_byte_list[0] + reversed_raw_byte_list[1] + reversed_raw_byte_list[2]

        #print "cory:%s:%s" % ( "{0:08b}".format(int(self.raw_byte_list[0],16)), reversed_raw_byte_list[0] )
        #self.pkt_binary = '0123456789abcdefghijABCD'
        #print "long_str:%s" % self.pkt_binary

        # Note:  The 2nd number in a slice is always 1 less than the one you want.  So if you want 0, you'd
        # have to say -1, but you cannot say -1, you must leave it empty!  This sucks.  Who thought of it!???

        # PID:
        bstr            = self.pkt_binary[7::-1]
        calc_pid        = '%0*X' % ((len(bstr) + 3) // 4, int(bstr, 2))
        # ADDR:
        bstr            = self.pkt_binary[14:7:-1]
        self.addr       = '%0*X' % ((len(bstr) + 3) // 4, int(bstr, 2))
        # ENDPT:
        bstr            = self.pkt_binary[18:14:-1]
        self.endpt      = '%0*X' % ((len(bstr) + 3) // 4, int(bstr, 2))
        # CRC5:
        bstr            = self.pkt_binary[23:18:-1]
        self.crc5       = '%0*X' % ((len(bstr) + 3) // 4, int(bstr, 2))

        printf( "pkt_binary=%s " % (self.pkt_binary) )
        printf( "==> calc_pid=0x%s addr=0x%s endpt=0x%s crc5=0x%s\n" % (calc_pid, self.addr, self.endpt, self.crc5) )
        #expected_crc = CRC().calc_crc5( self.pkt_binary[8:] )  # I thought the CRC was calculated w/o the PktID but 
        expected_crc = CRC().calc_crc5( self.pkt_binary )       # let's see if this works with all the pkt bits
        print( "   expected_crc=%s" % ( expected_crc[::-1] ) )


class Data0Packet( Packet ):
    'USB2 Data0 packet class - a child of the packet class'
    pkt_type    = 'DATA0'
    def __init__( self, pkt_data ):
        super( Data0Packet, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class Data1Packet( Packet ):
    'USB2 DATA1 packet class - a child of the packet class'
    pkt_type    = 'DATA1'
    def __init__( self, pkt_data ):
        super( Data1Packet, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class Data2Packet( Packet ):
    'USB2 DATA2 packet class - a child of the packet class'
    pkt_type    = 'DATA2'
    def __init__( self, pkt_data ):
        super( Data2Packet, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class MdataPacket( Packet ):
    'USB2 MDATA packet class - a child of the packet class'
    pkt_type    = 'MDATA'
    def __init__( self, pkt_data ):
        super( MdataPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class AckPacket( Packet ):
    'USB2 ACK packet class - a child of the packet class'
    pkt_type    = 'ACK'
    def __init__( self, pkt_data ):
        super( AckPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class NakPacket( Packet ):
    'USB2 NAK packet class - a child of the packet class'
    pkt_type    = 'NAK'
    def __init__( self, pkt_data ):
        super( NakPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class StallPacket( Packet ):
    'USB2 STALL packet class - a child of the packet class'
    pkt_type    = 'STALL'
    def __init__( self, pkt_data ):
        super( StallPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class NyetPacket( Packet ):
    'USB2 NYET packet class - a child of the packet class'
    pkt_type    = 'NYET'
    def __init__( self, pkt_data ):
        super( NyetPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class PrePacket( Packet ):
    'USB2 PRE packet class - a child of the packet class'
    pkt_type    = 'PRE'
    def __init__( self, pkt_data ):
        super( PrePacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class SplitPacket( Packet ):
    'USB2 SPLIT packet class - a child of the packet class'
    pkt_type    = 'SPLIT'
    def __init__( self, pkt_data ):
        super( SplitPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass

class PingPacket( Packet ):
    'USB2 PING packet class - a child of the packet class'
    pkt_type    = 'PING'
    def __init__( self, pkt_data ):
        super( PingPacket, self ).__init__( pkt_data )
    def __repr__( self ):
        return 'Pkt #%d : %s : raw_byte_list=%s' % (self.pkt_num, self.pkt_type, self.raw_byte_list)
    def _decodePkt( self ):
        pass


# -------------------------------------------------------------------------------- 

class ProtocolAnalyzer():
    'USB 2.0 Protocol Analyzer Class'
    device_name = ''    # Object var
    objcount = 0        # Class var
    dstype = ''         # Data Source Type ('csv' or 'serialport')
    dsname = ''         # Data Source Name (For CSV files: filename, for SERIALPORT: COM_port#)
    captured_pkts = []

    pid_dict = {
        'E1' : 'OUT',
        '69' : 'IN',
        'A5' : 'SOF',
        '2D' : 'SETUP',
        'C3' : 'DATA0',
        '4B' : 'DATA1',
        '87' : 'DATA2',
        '0F' : 'MDATA',
        'D2' : 'ACK',
        '5A' : 'NAK',
        '1E' : 'STALL',
        '95' : 'NYET',
        '3C' : 'PRE/ERR',
        '78' : 'SPLIT',
        'B4' : 'PING'
    }

    def __init__( self, name, ds_type, ds_name ):
        ProtocolAnalyzer.objcount += 1
        self.device_name = name
        self.dstype = ds_type
        self.dsname = ds_name
            
    def _processPkt( self, pkt_str ):
        'Processes a pkt string consisting of hex values separated by a space (eg: "41 8A 31 30")'
        pkt_byte_list = re.split( '\s*', pkt_str )
        if( pkt_byte_list[0] == 'E1' ):                         # OUT
            self.captured_pkts.append( OutPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == '69' ):                       # IN
            self.captured_pkts.append( InPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == 'A5' ):                       # SOF
            self.captured_pkts.append( SofPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == '2D' ):                       # SETUP
            self.captured_pkts.append( SetupPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == 'C3' ):                       # DATA0
            self.captured_pkts.append( Data0Packet(pkt_byte_list) )
        elif( pkt_byte_list[0] == '4B' ):                       # DATA1
            self.captured_pkts.append( Data1Packet(pkt_byte_list) )
        elif( pkt_byte_list[0] == '87' ):                       # DATA2
            self.captured_pkts.append( Data2Packet(pkt_byte_list) )
        elif( pkt_byte_list[0] == '0F' ):                       # MDATA
            self.captured_pkts.append( MdataPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == 'D2' ):                       # ACK
            self.captured_pkts.append( AckPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == '5A' ):                       # NAK
            self.captured_pkts.append( NakPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == '1E' ):                       # STALL
            self.captured_pkts.append( StallPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == '95' ):                       # NYET
            self.captured_pkts.append( NyetPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == '3C' ):                       # PRE/ERR
            self.captured_pkts.append( PrePacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == '78' ):                       # SPLIT
            self.captured_pkts.append( SplitPacket(pkt_byte_list) )
        elif( pkt_byte_list[0] == 'B4' ):                       # PING
            self.captured_pkts.append( PingPacket(pkt_byte_list) )
        else:
            print( '** ERROR ** : Unknown Pkt ID (%s)' % pkt_byte_list[0] )
            sys.exit(-1)
        #print( self.captured_pkts[-1] ) # print the last pkt

    def _startComport( self ):
        print( 'comport not supported yet' )
        sys.exit(-1)

    def _startCsv( self ):
        with open( self.dsname, 'rt' ) as f:
            for line in f:
                #process_line( line )
                if( not( line.startswith( '#' ) ) ):
                    line.strip()
                    try:
                        spd, spd_str, index, time, time_str, bytecnt, err, dev, ep, record, pkt_data, summary, pkt_ascii = re.split( ',', line )
                    except:
                        # Except clause entered when the split didn't return enough fields.  Ignore this line.
                        pass
                    else:
                        # Else clause entered if the split was successful.
                        valid_pkt = 1
                        txn_flag = record.find( 'txn' ) # find returns the index where first found or -1 if not found
                        if( txn_flag != -1 ):    # Skip transaction lines (only look at pkt lines)
                            valid_pkt = 0
                        if( len( pkt_data ) == 0 ):
                            valid_pkt = 0
                        # print( "record='%s' txn_flag=%d len_pkt_data=%d" % (record, txn_flag, len(pkt_data) ) )
                        if( valid_pkt ):
                            self._processPkt( pkt_data )
            
    def start( self ):
        if( self.dstype == 'csv' ):
            self._startCsv()
        elif( self.dstype == 'comport' ):
            self._startComport()
        else:
            print( '** Error ** : dstype %s not recognized' % self.dstype )
            sys.exit(-1)

    def displayPktsFormatted( self ):
        for pkt in self.captured_pkts:
            pkt.print_formatted()

