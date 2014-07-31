function varargout=normalize(varargin)

% function [levels_before,levels_after]=TVM_rms_mc(target_level)
%
% Can adjust levels of multichannel files (if comment is taken out). 
% Does adjustment for mean power over channels. target_level defines 
% the mean target level in dB.
% Note that _no_ per-channel adjustment, but an overall adjustment is
% achieved with this function.
% Main functionality is calculating rms before and after adjustment.
%
% USAGE: TVM_rms_mc(-26)

levAdj_r=varargin{1};
[filename,pathname]=uigetfile('*.wav','Browse for wav-data');

cd(pathname);
wavS=dir('*.wav');
mCar1=[];
all_rmsDB = [];
all_rmsDB_n = [];
for i=1:length(wavS)
    filename=wavS(i).name
    [Ar1,Fs,Bits]=wavread(filename);
    chan_n=size(Ar1,2);
    for k=1:chan_n
        rms(k)=norm(Ar1(:,k))/sqrt(length(Ar1(:,k)));    
        rmsDB(k)=20*log10(rms(k));
    end
    all_rmsDB = [all_rmsDB; rmsDB'];
    cAr1(i,1)=cellstr(filename);
    cAr1(i,2)=cellstr(num2str(rmsDB));
    mCar1=[mCar1;rms'];
    Ar2=Ar1*10^((levAdj_r-20*log10(mean(rms)))/20);
    for k=1:chan_n
        rms_n(k)=norm(Ar2(:,k))/sqrt(length(Ar1(:,k)));    
        rmsDB_n(k)=20*log10(rms_n(k));
    end
    all_rmsDB_n = [all_rmsDB_n; rmsDB_n'];    
    wavwrite(Ar2,Fs,[pathname 'rms_adj\' filename(1:(end-4)) '.wav']);    
end
    
% CellArray2File(cAr1,'u');

% varargout{1}=[max(mCar1);min(mCar1);20*log10(max(mCar1)/min(mCar1))];
varargout{1}=all_rmsDB;
varargout{2}=all_rmsDB_n;
