import random
import math
import argparse
import sys

try:
	parser = argparse.ArgumentParser(description='Example : python p2p5.py -S 100 -N 100 -M 10 -s 10 -u 1 -d 10 -detail 1')

	parser.add_argument('-S', action='store', help='File size in Mbits')
	parser.add_argument('-N', action='store', help='Number of peers')
	parser.add_argument('-M', action='store', help='Chunk size in Mbits')
	parser.add_argument('-s', action='store', help='Server upload speed in Mbps')
	parser.add_argument('-u', action='store', help='Peer upload speed in Mbps')
	parser.add_argument('-d', action='store', help='Peer download speed in Mbps')
	parser.add_argument('-detail', action='store', help='Enter 1 for detailed chunk transmissions or else enter 0')

	arguments = parser.parse_args()
	S = int(arguments.S)		# file size
	M = int(arguments.M)		# chunk size
	s = int(arguments.s)		# server upload
	u = int(arguments.u) 		# peer upload
	d = int(arguments.d) 		# peer download
	N = int(arguments.N)		# no of peers
	detail = int(arguments.detail)

	if(S<0 or S<M or N<0 or s<0 or u<0 or d<0 or (detail!=0 and detail!=1)):
		print ('\n\nNegative input not allowed.\n\n')


except:
	print ('\n\nInvalid input.\nEnter \'python p2p5.py --help\' to know more.\n\n')
	sys.exit()

time = 0
total_chunk_transferred = 0 			# variable to store total chunks transferred
total_chunk_transferred_sec = 0 		# variable to store total chunks that finished transfer in 'i'th second 
no_of_chunks = int(math.ceil(S/float(M)))

server_chunks = [1 for x in range(no_of_chunks)]

peers = [[0 for x in range(no_of_chunks)] for peer in range(N)]			# peers contain all peers and all chunks a peer has.

# peers[i][j] = 1 => means 'i'th peer has 'j'th chunk
# peers[i][j] = 0 => means 'i'th peer does not have 'j'th chunk
# peers[i][j] = 0.5 => means 'i'th peer is recieving 'j'th chunk

peers.append([1 for x in range(no_of_chunks)])							# add server as a peer. it contains all the chunks
																	
peers_bandwidth = [[u,d] for peer in range(N)]						# list to keep track of available upload and download bandwidth of each peer
peers_bandwidth.append([s])											# server does not download anything

peers_bandwidth_update = []

def distribution_complete():
	# function checks if distribution is complete
	global peers
	for peer in peers:
		for chunk in peer:
			if chunk is 0:
				return False
	return True

def chunk_availability(chunk):
	# returns a list of peers which contain a particular chunk
	global peers
	peers_with_chunk = []
	for i,peer in enumerate(peers):
		if(peer[chunk] == 1):
			peers_with_chunk.append(i)
	return peers_with_chunk

def display():
	# display function is called after each second to print all chunk transfers
	global total_chunk_transferred_sec,total_chunk_transferred,time
	if (detail==1):
		print ('-'*60)
	print (str(time)+'\t\t'+str(total_chunk_transferred_sec)+'\t\t\t'+str(total_chunk_transferred))
	if (detail==1):
		print ('-'*60)
	total_chunk_transferred_sec=0

def bandwidth_refresh():
	# function which updates peers' bandwidth after chunk transfer is complete
	global peers_bandwidth_update,total_chunk_transferred,total_chunk_transferred_sec,peers,time
	time += 1
	
	for i,info in enumerate(peers_bandwidth_update):					# info = [peer,time,bnadwidth,u/d,chunk] u=0 d=1
		info[1] = info[1] - 1
	i=0
	loop = len(peers_bandwidth_update)
	update_peers = []
	while (i<loop):
		info = peers_bandwidth_update[i]
		if(info[1] == 0):
			peers_bandwidth[info[0]][info[3]] = peers_bandwidth[info[0]][info[3]] + info[2]
			if(info[3] == 1):
				test_peer = info[0]
				peers[info[0]][info[4]] = 1
				total_chunk_transferred += 1
				total_chunk_transferred_sec += 1
			update_peers.append(i)
		i+=1
	c=0	
	for i in update_peers:
		peers_bandwidth_update.pop(i-c)
		c+=1
print ('')	
print ('time in sec\tchunks transferred\ttotal chunks transferred')

while(True):
	peer_range=range(0,len(peers)-1)
	for x in range(len(peers)-1):
		peer_no = random.choice(peer_range)			# chooses peers randomly but all peers are visited every second
		peer = peers[peer_no]
		peer_range.remove(peer_no)
		
		required_chunks = []
		required_chunk = None
		selected_peer = None
		
		for i,chunk in enumerate(peer):
			if (chunk==0):
				required_chunks.append(i)		# creates a list of chunks required
		rarity = []
		if(len(required_chunks) > 0):
			for i,chunk in enumerate(required_chunks):					# now find the rarest of it. rarity is a 2-tuple list => (chunk,peers containing that chunk)
				rarity.append((chunk,len(chunk_availability(chunk))))
			rarity.sort(reverse=True, key=lambda x:x[1])
		
		while(len(rarity)>0):
			required_chunk,rare_factor = rarity.pop()			# choose peers in decreasing order of rarity
			chunk_found = False
			chunk_possibility = False
			if(required_chunk is not None):					
				peers_with_chunk = chunk_availability(required_chunk)   # creates a list of peers which have the selected
				for peer in peers_with_chunk:
					if(peers_bandwidth[peer][0] > 0):
						selected_peer = peer 							# check the peer list for bandwidth availability and select a peer
						chunk_possibility = True				
						break
			
			current_peer = peer_no
		
			if(peers_bandwidth[current_peer][1] > 0 and (chunk_possibility is True)):	# there is chunk to be downloaded and the peer has bandwidth
				chunk_found = True
				chunk = required_chunk
				time_for_chunk = 0.0
				transfer_speed = 0
				
				selected_peer_upload = peers_bandwidth[selected_peer][0]		# selected peer is the sending peer
				current_peer_download = peers_bandwidth[current_peer][1]		# current peer is the reciveing peer
				
				# transmission always takes place at maximum speed possible
				if(current_peer_download > selected_peer_upload):			# sending peer's bandwidth is the bottleneck
					peers_bandwidth[current_peer][1] = peers_bandwidth[current_peer][1] - selected_peer_upload				#bandwith is 2-tuple. 0-upload 1-download
					time_for_chunk = int(M/float(selected_peer_upload))			# time for current chunk transmission
					transfer_speed = selected_peer_upload

					peers_bandwidth[selected_peer][0] = 0				# selected peer's bandwidth will be 0 ans=d hence it will be busy for this time
					peers[current_peer][chunk] = 0.5					# peer is under transmission. not fit for upload or download
					
					peers_bandwidth_update.append([current_peer,time_for_chunk,selected_peer_upload,1,chunk])		# after "time_for_chunk" seconds selected_peer and current_peer's bandwidth have to updated.
					peers_bandwidth_update.append([selected_peer,time_for_chunk,selected_peer_upload,0])
				elif(selected_peer_upload > current_peer_download):				# recieving peer's bandwidth is the bottleneck
					peers_bandwidth[selected_peer][0] -= current_peer_download
					time_for_chunk = int(M/float(current_peer_download))
					transfer_speed = current_peer_download

					peers_bandwidth[current_peer][1] = 0
					peers[current_peer][chunk] = 0.5
							
					peers_bandwidth_update.append([current_peer,time_for_chunk,current_peer_download,1,chunk])
					peers_bandwidth_update.append([selected_peer,time_for_chunk,current_peer_download,0])
				else:
					time_for_chunk = int(M/float(current_peer_download))
					peers_bandwidth[current_peer][1] = 0
					peers_bandwidth[selected_peer][0] = 0
					transfer_speed = current_peer_download

					peers[current_peer][chunk] = 0.5
					peers_bandwidth_update.append([current_peer,time_for_chunk,selected_peer_upload,1,chunk])
					peers_bandwidth_update.append([selected_peer,time_for_chunk,selected_peer_upload,0])
						
			if (chunk_found is True):
				if(detail==1):
					print ('peer '+str(current_peer)+' recives chunk '+str(chunk)+' from peer '+str(selected_peer)+' at '+str(transfer_speed)+' Mbps for '+str(time_for_chunk)+' secs')
				break
			
	bandwidth_refresh()

	display()
	
	if(distribution_complete() is True):
		display()
		break
	

				
