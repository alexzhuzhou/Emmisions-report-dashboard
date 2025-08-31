import React from 'react';
import { Modal as MuiModal, Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '100%',
  maxWidth: '600px',
  outline: 'none',
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 2.5,
  borderRadius: 4,
};

export const Modal: React.FC<ModalProps> = ({
  open,
  onClose,
  title,
  children,
  maxWidth = 'sm',
}) => {
  return (
    <MuiModal
      open={open}
      onClose={onClose}
      aria-labelledby="modal-title"
      aria-describedby="modal-description"
    >
      <Box sx={{ ...style, maxWidth: '750px' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          {title && (
            <Typography id="modal-title" variant="h6" component="h2" sx={{color: '#2f2f2f', fontSize: '22px', fontWeight: 600}}>
              {title}
            </Typography>
          )}
          <IconButton
            onClick={onClose}
            sx={{ ml: 'auto' }}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </Box>
        <Box id="modal-description">
          {children}
        </Box>
      </Box>
    </MuiModal>
  );
};
