import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import axios from "axios";


function timeDifferenceDescription(previousTime) {
  if (!previousTime) {
    return "Never Updated Since Load";
  }

  const now = new Date();
  const previous = new Date(previousTime); // Ensure input is a Date object
  const deltaMs = now - previous; // Time difference in milliseconds

  if (isNaN(previous.getTime())) {
    return "Invalid Date";
  }

  const deltaSeconds = Math.floor(deltaMs / 1000);
  const deltaMinutes = Math.floor(deltaSeconds / 60);
  const deltaHours = Math.floor(deltaMinutes / 60);
  const deltaDays = Math.floor(deltaHours / 24);

  if (deltaDays > 30) {
    return `More than 30 days ago @ ${previous.toLocaleString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })}`;
  }

  if (deltaDays >= 1) {
    return `${deltaDays} day${deltaDays > 1 ? 's' : ''} ago`;
  }

  if (deltaHours >= 1) {
    return `${deltaHours} hour${deltaHours > 1 ? 's' : ''} ago`;
  }

  if (deltaMinutes >= 1) {
    return `${deltaMinutes} minute${deltaMinutes > 1 ? 's' : ''} ago`;
  }

  return "Just now";
}



const SiteManager = () => {
  const [notificationSites, setNotificationSites] = useState([]);
  const [pendingSites, setPendingSites] = useState([]);
  const [userAddingSite, setUserAddingSite] = useState({ url: "" });
  const [sortNotificationByLatest, setSortNotificationByLatest] = useState(false);

  const fetchSites = async (route) => {
    const setter = {
      notification: setNotificationSites,
      pending: setPendingSites,
    }[route];

    try {
      const response = await axios.get(`/api/${route}`);
      setter(response.data);
    } catch (error) {
      console.error(`Error fetching sites: ${route}`, error);
    }
  };

  const refresh = async () => {
    await fetchSites("notification");
    await fetchSites("pending");
  };

  // Refresh every 30 minutes
  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30 * 60 * 1000); 
    return () => clearInterval(interval);
  }, []);

  const addSite = async () => {
    try {
      await axios.post("api/pending", userAddingSite);
      setUserAddingSite({ url: "" });
      await fetchSites("pending");
    } catch (error) {
      console.error("Error adding site:", error);
    }
  };

  const deleteSite = async (route, url) => {
    // pending | notification

    // url can't just go directly as it will change path | query will be messing with the path
    const encodedUrl = encodeURIComponent(url);
    try {
      await axios.delete(`api/${route}/${encodedUrl}`);
      await fetchSites(route);
    } catch (error) {
      console.error("Error deleting site:", error);
    }
  };

  const refreshDatabase = async () => {
    try {
      await axios.post("api/refresh");
    } catch (error) {
      console.log("Error refreshing site:", error)
    }
  }

  return (
    <Box sx={{ padding: 4 }}>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h4" gutterBottom>
          Site Manager
        </Typography>
        <Button variant="contained" color="primary" onClick={refresh}>
          Refresh
        </Button>
        <Button variant="outlined" color="primary" onClick={() => {
          if (window.confirm(`Do you really want move all to pending?`)){
            refreshDatabase();
            refresh();
          }
        }}>
          Move All From Notification To Pending
        </Button>
      </Box>

      <Typography variant="h5">Notification Sites</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>

              <TableCell>Latest Update
                <Button
                  style={{
                    backgroundColor: sortNotificationByLatest ? "#d8e5f3" : "",
                  }}
                  onClick={()=>setSortNotificationByLatest(!sortNotificationByLatest)}
                >

                  &#x21C5;
                </Button> 
              </TableCell>

              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(sortNotificationByLatest 
            ? [...notificationSites].sort((a, b) => new Date(b["latest-updated-date"]) - new Date(a["latest-updated-date"]))
            : notificationSites )
            .map((site) => (
              <TableRow key={site.url}>
                <TableCell>
                  <a href={site.url} target="_blank" rel="noopener noreferrer">
                    {site.title}
                  </a>
                </TableCell>

                <TableCell>{timeDifferenceDescription(site["latest-updated-date"])}</TableCell>

                <TableCell>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() =>
                      window.confirm(`Do you really want delete ${site.title} - ${site.url}`) &&
                      deleteSite("notification", site.url)
                    }
                  >
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <br />
      <br />
      <br />
      <br />

      <Typography variant="h5">Pending Sites</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>URL</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            <TableRow key="input-form">
              <TableCell>
                <TextField
                  label="Enter URL"
                  variant="outlined"
                  size="small"
                  value={userAddingSite.url}
                  onChange={(e) => setUserAddingSite({ url: e.target.value })}
                  placeholder="e.g., https://example.com" // Default gray text when empty
                  fullWidth
                />
              </TableCell>
              <TableCell>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={addSite} // Function to add the new URL
                >
                  Add
                </Button>
              </TableCell>
            </TableRow>

            {pendingSites.map((site) => (
              <TableRow key={site}>
                <TableCell>
                  <a href={site} target="_blank" rel="noopener noreferrer">
                    {site}
                  </a>
                </TableCell>
                <TableCell>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => deleteSite("pending", site)}
                  >
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>

    
  );
};

export default SiteManager;
