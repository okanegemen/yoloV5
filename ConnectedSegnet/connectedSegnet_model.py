from connectedSegenet_elements import *
import torch
import torch.nn as nn



class ConSegnetsModel(nn.Module):
    def __init__(self,in_channels):
        super(ConSegnetsModel).__init__()
        self.in_channels = in_channels
        self.encoderBlock1 = DoubleConv(in_channels,64,encoder=True)
        self.secondFirst = DoubleConv(64,64,encoder=True)
        self.encoderBlock2 = DoubleConv(64,128,encoder=True)
        self.encoderBlock3 = TripleConv(128,256,encoder=True)
        self.encoderBlock4 = TripleConv(256,512,encoder=True)
        self.encoderBlock5 = DoubleConv(512,512,encoder=True)

        #this conv block to second segnet.Second segnet's last conv block  have 3 convolutional layer
        self.extraEncoder = TripleConv(512,512,True)
        #################################
        self.decoderBlock1 = TripleConv(512,512)
        self.decoderBlock2 = TripleConv(512,512)
        self.decoderBlock3 = TripleConv(512,256)
        self.decoderBlock4 = DoubleConv(256,128)
        self.decoderBlock5 = nn.Conv2d(128,64,3,padding=1)
        self.dilation = dilationConv(64,64)
        self.conv1x1 = conv1x1(in_channels=64,out_channels=1)
    def forward(self,input_image):
#FIRST SEGNET MODEL
        #ENCODER STAGE---->1
        dim_0 = input_image.size()
        out1=self.encoderBlock1(input_image)
        out1,indices_1= maxpooling(out1)
        #ENCODER STAGE----->2
        dim_1 = out1.size()
        out2=self.encoderBlock2(out1)
        out2,indices_2=maxpooling(out2)
        #ENCODER STAGE----->3
        dim_2 = out2.size()

        out3 = self.encoderBlock3(out2)
        out3,indices_3= maxpooling(out3)
        #ENCODER STAGE----->4
        dim_3 = out3.size()
        out4 = self.encoderBlock4(out3)
        out4,indices_4 = maxpooling(out4)
        #ENCODER STAGE----->5
        dim_4 = out4.size()
        out5  = self.encoderBlock5(out4)
        out5,indices_5=maxpooling(out5)
        dim_5 =out5.size()
        #DECODER STAGE----->5
        dec_out1 = unmaxpooling(out5,maxpool_indices=indices_5,dim=dim_5)
        dec_out1 = self.decoderBlock1(dec_out1)
        dec_d1=dec_out1.size()
        #DECODER STAGE----->4
        dec_out2 = unmaxpooling(out4,maxpool_indices=indices_4,dim=dim_4)
        dec_out2 = self.decoderBlock2(dec_out2)
        dec_d2 = dec_out2.size()
        #DECODER STAGE----->3
        dec_out3 = unmaxpooling(out3,maxpool_indices=indices_3,dim=dim_3)
        dec_out3 = self.decoderBlock3(dec_out3)
        dec_d3 = dec_out3.size()
        #DECODER STAGE----->2
        dec_out4 = unmaxpooling(out2,maxpool_indices=indices_2,dim=dim_2)
        dec_out4 = self.decoderBlock2(dec_out4)
        dec_d4 = dec_out4.size()
        #DECODER STAGE----->1
        dec_out5 = unmaxpooling(out1,maxpool_indices=indices_1,dim=dim_1)
        dec_out5 = self.decoderBlock5(dec_out5)
        dec_d5 = dec_out5.size()
#SECOND SEGNET MODEL
        #SECOND ENCODER STAGE---->1

        sec_en_out1 = self.secondFirst(dec_out5)
        sec_en_out1,indices_sec_1 = maxpooling(sec_en_out1)
        sec_en_out1 = cat(sec_en_out1,dec_out4)
        sec_dim_1 = sec_en_out1.size()

        #SECOND ENCODER STAGE---->2
        sec_en_out2 = self.encoderBlock2(sec_en_out1)
        sec_en_out2,indices_sec_2 = maxpooling(sec_en_out2)
        #concate output and third output of decoder
        sec_en_out2=cat(sec_en_out2,dec_out3)
        #finding dimension to upscaling
        sec_dim_2 = sec_en_out2.size()
        #SECOND ENCODER STAGE----->3
        sec_en_out3 = self.encoderBlock3(sec_en_out2)
        sec_en_out3 ,indices_sec_3 = maxpooling(sec_en_out3)
        sec_en_out3 = cat(sec_en_out3,dec_out2)
        sec_dim_3 = sec_en_out3.size()
        #SECOND ENCODER STAGE----->2
        sec_en_out4 = self.encoderBlock4(sec_en_out3)
        sec_en_out4,indices_sec_4 = maxpooling(sec_en_out4)
        sec_en_out4 = cat(sec_en_out4,dec_out1)
        sec_dim_4 = sec_en_out4.size()
        #SECOND ENCODER STAGE----->1
        sec_en_out5 = self.extraEncoder(sec_en_out5)
        sec_en_out5,indices_sec_5 = maxpooling(sec_en_out5)
        sec_dim_5 = sec_en_out5.size()


        #SECOND DECODER STAGE----->5
        sec_dec_out1 = unmaxpooling(sec_en_out5,maxpool_indices=indices_sec_5,dim=sec_dim_5)
        sec_dec_out1 = self.decoderBlock1(sec_dec_out1)
        sec_dec_d1 = sec_dec_out1.size()
        #SECOND DECODER STAGE----->4
        sec_dec_out2 = unmaxpooling(sec_dec_out1,maxpool_indices=indices_sec_4,dim=sec_dim_4)
        sec_dec_out2 = self.decoderBlock2(sec_dec_out2)
        sec_dec_d2 = sec_dec_out2.size()
        #SECOND DECODER STAGE----->3
        sec_dec_out3 = unmaxpooling(sec_dec_out2,maxpool_indices=indices_sec_3,dim=sec_dim_3)
        sec_dec_out3 = self.decoderBlock3(sec_dec_out3)
        sec_dec_d3 = sec_dec_out3.size()
        #SECOND DECODER STAGE----->2
        sec_dec_out4 = unmaxpooling(sec_dec_out3,maxpool_indices=indices_sec_2,dim=sec_dim_2)
        sec_dec_out4 = self.decoderBlock4(sec_dec_out4)
        sec_dec_d4 = sec_dec_out4.size()
        #SECOND DECODER STAGE----->1
        sec_dec_out5 = unmaxpooling(sec_dec_out4,maxpool_indices=indices_sec_1,dim=sec_dim_1)
        sec_dec_out5=self.decoderBlock5(sec_dec_out5)
        sec_dec_d5 = sec_dec_out5.size()
        dilation_out= self.dilation(sec_dec_out5)
        out = self.conv1x1(dilation_out)

        return out


        



