
import numpy as np
import os
from datetime import datetime
from pynwb import NWBFile
from pynwb import TimeSeries
from pynwb.behavior import Position
from pynwb import NWBHDF5IO
from pynwb.file import Subject

data_dir = "./session data/"
save_dir = "./NWB1.5.1/"

subjects = os.listdir(data_dir)

for subject in subjects:
     subject_dir = data_dir + subject + "/"
     subject_number = subject[-4:]
     experiments = os.listdir(subject_dir)

     for experiment in experiments:
         experiment_dir = subject_dir + experiment + "/"
         sessions = os.listdir(experiment_dir)
         if experiment == 'ARHMM': #leave out ARHMM data for now
             continue

         frame_data_exists = False
         trial_data_exists = False
         sniff_signal_exists = False

         for session in sessions:
             session_dir = experiment_dir + session + "/"
             session_number = session[-2:]
             if session_number == 'nt': #skip pre-implant data
                 continue

             #Neurodata Without Borders file settings
             nwb_description = "Experiment type: " + experiment + ", " + subject + ", " + session
             print(nwb_description)
             nwb_identifier = subject_number + '_' + experiment + '_' + session_number
             io = NWBHDF5IO(save_dir + nwb_identifier + '.nwb', mode='w')

             dateinfo = "2021-01-01, 01:00:00"
             session_date_info = datetime.strptime(dateinfo, "%Y-%m-%d,%H:%M:%S")
             if os.path.exists(session_dir + "notes.txt") == True:
                 with open(session_dir + "notes.txt") as f:
                     notes = f.readlines()
                     for line in range(0,len(notes)):
                         if 'Date' in notes[line]:
                             dateinfo = notes[line]
                             dateinfo = dateinfo[6:26]
                             if dateinfo[14] == '-':
                                 session_date_info = datetime.strptime(dateinfo, "%Y-%m-%d: %H-%M-%S")
                             else:
                                 session_date_info = datetime.strptime(dateinfo, "%Y-%m-%d, %H:%M:%S")

             if os.path.exists(session_dir + "trial_params.txt") == True:
                 #sampled by trial
                 trial_data_exists = True
                 trial_params = np.genfromtxt(session_dir + "trial_params.txt",delimiter = ',',skip_header=0)
                 concentration_level = trial_params[:,0]
                 stimulus_side = trial_params[:,1]
                 chosen_side = trial_params[:,2]
                 trial_start = trial_params[:,3]
                 trial_end = trial_params[:,4]

             if os.path.exists(session_dir + "frame_params_wITI.txt") == True: #sampled at 80 Hz
                 frame_data_exists = True
                 frame_params = np.genfromtxt(session_dir + "frame_params_wITI.txt",delimiter = ',',skip_header=0)
                 nose_x = frame_params[:,0]; nose_y = frame_params[:,1]
                 head_x = frame_params[:,2]; head_y = frame_params[:,3]
                 body_x = frame_params[:,4]; body_y = frame_params[:,5]
                 frame_msec = frame_params[:,7]

             if os.path.exists(session_dir + "sniff.bin") == True:
                 #sampled at 800 Hz
                 sniff_signal_exists = True
                 sniff_signal = np.fromfile(session_dir + "sniff.bin",dtype = 'float')

             #create a session-specific neurodata without borders file
             subject_info = Subject(age=None, description=None,
                                    genotype=None, sex=None, species='Mouse', subject_id=subject,
                                    weight=None, date_of_birth=None, strain='B6')
             nwbfile = NWBFile(session_description=nwb_description,  #required
                               identifier=nwb_identifier,  # required
                               session_start_time=session_date_info,  #required
                               subject = subject_info,
                               session_id=session, #optional
                               file_create_date= session_date_info)  #optional

             if trial_data_exists == True:
                 nwbfile.add_trial_column(name='level', description='the level of odor concentration stimulus presented')
                 nwbfile.add_trial_column(name='side', description='which side of the assay the correct stimulus is presented on')
                 nwbfile.add_trial_column(name='chosen', description='which side of the assay the mouse chose (correct or incorrect)')

                 for trial in range(0,len(concentration_level)):
                     nwbfile.add_trial(start_time=trial_start[trial],
                                       stop_time=trial_end[trial],
                                       level=concentration_level[trial],side=stimulus_side[trial],
                                       chosen=chosen_side[trial])

             if frame_data_exists == True:
                 tracking = Position() #create a position container for tracking data
                 tracking.create_spatial_series(name='nose x-position',
                                                data=nose_x,
                                                timestamps=frame_msec,
                                                reference_frame='session start')
                 tracking.create_spatial_series(name='nose y-position',
                                                data=nose_y,
                                                timestamps=frame_msec,
                                                reference_frame='session start')
                 tracking.create_spatial_series(name='head x-position',
                                                data=head_x,
                                                timestamps=frame_msec,
                                                reference_frame='session start')
                 tracking.create_spatial_series(name='head y-position',
                                                data=head_y,
                                                timestamps=frame_msec,
                                                reference_frame='session start')
                 tracking.create_spatial_series(name='body x-position',
                                                data=body_x,
                                                timestamps=frame_msec,
                                                reference_frame='session start')
                 tracking.create_spatial_series(name='body y-position',
                                                data=body_y,
                                                timestamps=frame_msec,
                                                reference_frame='session start')

             if sniff_signal_exists == True:
                 sniff = TimeSeries(name='sniff_signal', data=sniff_signal, unit='V', starting_time=0.0, rate=0.00125)
                 nwbfile.add_acquisition(sniff)

             io.write(nwbfile)
             io.close()